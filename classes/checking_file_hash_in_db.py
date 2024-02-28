import os
import mysql.connector
import concurrent.futures
import time
class CheckingFileName:
    def __init__(self):
        # MySQL connection configuration
        self.mysql_config = {
            'host': 'localhost',
            'user': 'root',
            'password': '',
            'database': 'info_pemilu',
        }
        self.not_found_files = []
        # Directory containing your files
        self.directory_path = None
        # Output file for not found files
        self.not_found_file_path = 'not_found_files.txt'
        # List to store not found files
        self.not_found_files = []

    def process_files(self, root, files):
        # Establish a MySQL connection
        connection = mysql.connector.connect(**self.mysql_config)

        # Create a cursor object to interact with the database
        cursor = connection.cursor()

        try:
            for filename in files:
                if filename.endswith('.json'):  # Adjust the file extension accordingly
                    # Get the file name without directory and extension
                    base_name = os.path.splitext(os.path.basename(filename))[0]

                    # Construct and execute a SELECT query
                    query = f"SELECT * FROM calons WHERE md5(foto) = '{base_name}'"
                    cursor.execute(query)

                    # Fetch the result (assuming you expect only one row)
                    result = cursor.fetchone()

                    if result is None:
                        # File not found in the database
                        print(os.path.join(root, filename))
                        self.not_found_files.append(os.path.join(root, filename))
        finally:
            # Close the cursor and connection
            cursor.close()
            connection.close()

    def process(self, path=''):
        # Record the start time
        start_time = time.time_ns()
        self.directory_path = path

        # Iterate over the root directory and its subdirectories
        pool = concurrent.futures.ThreadPoolExecutor(max_workers=200)
        for root, _, files in os.walk(self.directory_path):
            pool.submit(self.process_files, root=root, files=files)
        pool.shutdown(wait=True)

        # Write not found files to the output file
        with open(f"{self.directory_path}/{self.not_found_file_path}", 'w') as not_found_file:
            for file_path in self.not_found_files:
                not_found_file.write(file_path + '\n')

        # Record the end time
        end_time = time.time_ns()

        # Calculate the duration
        duration = (end_time - start_time) / 1000

        print(f"Duration: {duration:.2f} seconds")
