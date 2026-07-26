from kafka import KafkaProducer

producer = KafkaProducer(
    bootstrap_servers='localhost:9092'
)

producer.send('raw.logs', b'hello soc')
producer.flush()

print("Message sent")