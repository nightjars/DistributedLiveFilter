class MeasurementSource:
    
    pass

class RabbitMQSource:
    class MeasurementPoller:
        def __init__(self, output_queue):
            self.output_queue = output_queue
            self.terminated = False

            # self.config = DataLoader.load_data_from_text_files(sites_data_file=DataStructures.configuration['sites_file'],
            #                                                   faults_data_file=DataStructures.configuration['faults_file'])

        def send_measurement(self, measurement):
            self.output_queue.put(measurement)

        def start(self):
            pass

        def stop(self):
            self.terminated = True

    class RabbitMQPoller(MeasurementPoller):
        poller_instance = None

        def __init__(self, output_queue):
            super(RabbitMQPoller, self).__init__(output_queue)
            threading.Thread(target=self.rabbit_poller).start()
            RabbitMQPoller.poller_instance = self

        @staticmethod
        def message_callback(msg):
            RabbitMQPoller.poller_instance.send_measurement(json.loads(msg.body))

        def rabbit_poller(self):
            connection = amqp.Connection(
                host=DataStructures.configuration['rabbit_mq']['host'],
                userid=DataStructures.configuration['rabbit_mq']['userid'],
                password=DataStructures.configuration['rabbit_mq']['password'],
                virtual_host=DataStructures.configuration['rabbit_mq']['virtual_host'],
                exchange=DataStructures.configuration['rabbit_mq']['exchange_name']
            )
            print("about to connect")
            connection.connect()
            print("connected")
            channel = connection.channel()
            channel.exchange_declare(DataStructures.configuration['rabbit_mq']['exchange_name'],
                                     'test_fanout', passive=True)
            queue_name = channel.queue_declare(exclusive=True)[0]
            channel.queue_bind(queue_name, exchange=DataStructures.configuration['rabbit_mq']['exchange_name'])
            channel.basic_consume(callback=RabbitMQPoller.message_callback,
                                  queue=queue_name,
                                  no_ack=True)
            print("about to start consuming")
            while not self.terminated:
                connection.drain_events()
            connection.close()