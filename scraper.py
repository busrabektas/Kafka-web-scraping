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

'''

    This python file scrapes the product information from the first page of the https://scrapeme.live/shop/ website and saves this data in a JSON file. It also creates a Kafka topic called "digitalbrain" and writes the scraped data as JSON messages to this topic.

'''


#URL to scrape
URL = "https://scrapeme.live/shop/"
KAFKA_TOPIC = 'digitalbrain'
KAFKA_BOOTSTRAP_SERVERS = ["kafka:9093"]

#List to store product information
product_infos = []


#Function to create a Kafka topic
def create_topic():

    # Retry mechanism for connectiong to Kafka brokers
    for _ in range(5):
        try:
            # Instance of the KafkaAdminClient
            admin_client = KafkaAdminClient(
                bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
                api_version=(2, 8, 1)
            )

            #New topic called digitalbrain defined
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
            time.sleep(0.5)

    raise Exception("Failed to connect to Kafka brokers after several retries")

#Function to initialize a Kafka producer
def start_producer():
    producer = KafkaProducer(bootstrap_servers=["kafka:9093"],
                             api_version=(2,8,1),
                             value_serializer=lambda v: json.dumps(v, ensure_ascii=False, indent=2).encode('utf-8'))
    return producer

#Function to scrape product details from a given URL
def scrape_product_details(product_url):

    response = requests.get(product_url)
    soup = BeautifulSoup(response.text, 'html.parser')
    
    #Extracting description and stock information 
    description = soup.select_one("div.woocommerce-product-details__short-description").get_text(strip=True) if soup.select_one("div.woocommerce-product-details__short-description") else "No description"
    stock = soup.select_one("p.stock.in-stock").get_text() if soup.select_one("p.stock.in-stock") else "Out of stock"
    
    return description, stock


def scrape_data():

    #create the kafka topic via create_topic method
    create_topic()

    #Request the webpage and parse with BeautifulSoup 
    response = requests.get(URL)
    soup = BeautifulSoup(response.text, 'html.parser')
    product_elements = soup.select("li.product")
    #print("PRODUCT", product_elements)
    print("Product elements count:", len(product_elements))

    #Initialize Kafka producer
    producer = start_producer()
    print(producer)

    #Loop through each product elemetn on the website
    for product in product_elements:

        #Extract relevant information (name,price,product link)
        name = product.select_one("h2.woocommerce-loop-product__title").get_text()
        price = product.select_one("span.woocommerce-Price-amount.amount").get_text()
        product_url = product.select_one("a.woocommerce-LoopProduct-link")["href"]
        
        description, stock = scrape_product_details(product_url)
        
        #Store product information in a list
        product_infos.append({'name': name,
                        'price': price,
                        'description': description,
                        'stock': stock})
        #Prepare data for Kafka message 
        data = {'name': name,
                'price': price,
                'description': description,
                'stock': stock}
        
        # Send message to Kafka topic 
        producer.send(KAFKA_TOPIC, data)

        # Ensure all messages are sent before exiting
        producer.flush()
        print("done") #print done for all product 

    #Save scraped data to a JSON file
    json_path = '/app/data/data.json'    
    with open(json_path, 'w', encoding='utf-8') as file:
        json.dump(product_infos, file, ensure_ascii=False, indent=2)

    #Consume messages from Kafka topic 
    consumer = KafkaConsumer(
        KAFKA_TOPIC,
        bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
        api_version=(2,8,1),
        auto_offset_reset='earliest',
        max_poll_records = 100,
        value_deserializer=lambda x: x.decode('utf-8')
        )
    
    #Print messages
    records = consumer.poll(timeout_ms=sys.maxsize)
    for tp, records_list in records.items():
        for record in records_list:
            print(record.value)

    
    return "DONE!"

if __name__ == "__main__":
    scrape_data()
