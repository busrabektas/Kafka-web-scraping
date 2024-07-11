import sys
import requests
from bs4 import BeautifulSoup
import json
import time
from kafka import KafkaProducer, KafkaConsumer
from kafka.structs import TopicPartition

from kafka import KafkaAdminClient
from kafka.admin import NewTopic
from kafka.errors import TopicAlreadyExistsError, NoBrokersAvailable


URL = "https://scrapeme.live/shop/"
KAFKA_TOPIC = 'digitalbrain'
KAFKA_BOOTSTRAP_SERVERS = ["kafka:9093"]

product_infos = []


def create_topic():
    # Retry mechanism
    for _ in range(5):
        try:
            # Create an instance of the KafkaAdminClient
            admin_client = KafkaAdminClient(
                bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
                api_version=(2, 8, 1)
            )

            # Define the new topic
            topic_name = "digitalbrain"
            num_partitions = 1
            replication_factor = 1

            new_topic = NewTopic(
                name=topic_name, 
                num_partitions=num_partitions, 
                replication_factor=replication_factor
            )

            # Create the topic
            try:
                admin_client.create_topics(new_topics=[new_topic], validate_only=False)
                print(f"Topic '{topic_name}' created successfully.")
            except TopicAlreadyExistsError:
                print(f"Topic '{topic_name}' already exists.")
            except Exception as e:
                print(f"An error occurred: {e}")

            # Close the admin client
            admin_client.close()
            return
        except NoBrokersAvailable:
            print("No brokers available. Retrying in 5 seconds...")
            time.sleep(5)

    raise Exception("Failed to connect to Kafka brokers after several retries")


def start_producer():
    producer = KafkaProducer(bootstrap_servers=["kafka:9093"],
                             api_version=(2,8,1),
                             value_serializer=lambda v: json.dumps(v, ensure_ascii=False, indent=2).encode('utf-8'))
    return producer

def scrape_product_details(product_url):
    response = requests.get(product_url)
    soup = BeautifulSoup(response.text, 'html.parser')
    
    description = soup.select_one("div.woocommerce-product-details__short-description").get_text(strip=True) if soup.select_one("div.woocommerce-product-details__short-description") else "No description"
    stock = soup.select_one("p.stock.in-stock").get_text() if soup.select_one("p.stock.in-stock") else "Out of stock"
    
    return description, stock

def scrape_data():


    create_topic()
    response = requests.get(URL)
    soup = BeautifulSoup(response.text, 'html.parser')
    product_elements = soup.select("li.product")
    #print("PRODUCT", product_elements)
    print("Product elements count:", len(product_elements))

    producer = start_producer()
    print(producer)

    for product in product_elements:

        name = product.select_one("h2.woocommerce-loop-product__title").get_text()
        price = product.select_one("span.woocommerce-Price-amount.amount").get_text()
        product_url = product.select_one("a.woocommerce-LoopProduct-link")["href"]
        
        description, stock = scrape_product_details(product_url)
        
        product_infos.append({'name': name,
                        'price': price,
                        'description': description,
                        'stock': stock})
        data = {'name': name,
                'price': price,
                'description': description,
                'stock': stock}
        
        # Sending a simple string message
        producer.send(KAFKA_TOPIC, data)

        # Ensure all messages are sent before exiting
        producer.flush()
        print("done")

        
    with open('data.json', 'w', encoding='utf-8') as file:
        json.dump(product_infos, file, ensure_ascii=False, indent=2)

    #### show topic messages
    consumer = KafkaConsumer(
        KAFKA_TOPIC,
        bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
        api_version=(2,8,1),
        auto_offset_reset='earliest',
        max_poll_records = 100,
        value_deserializer=lambda x: x.decode('utf-8')
        )
    
#    records = consumer.poll(timeout_ms=sys.maxsize)
    records = consumer.poll(timeout_ms=sys.maxsize)
    for tp, records_list in records.items():
        for record in records_list:
            print(record.value)

    
    return "DONE!"

if __name__ == "__main__":
    scrape_data()
