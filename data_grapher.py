import matplotlib.pyplot as plt
import numpy as np
import os
import csv

def plot(data_array, title):
	eje_x = np.array([float(row[4].strip()) for row in data_array])  # Quinto valor
	angulo_1 = np.array([float(row[0].strip()) for row in data_array])  # Primer valor
	angulo_2 = np.array([float(row[1].strip()) for row in data_array])  # Segundo valor

	# Graficar los datos
	plt.figure(figsize=(10, 6))
	plt.plot(eje_x, angulo_1, label='Ángulo 1', marker='o')
	plt.plot(eje_x, angulo_2, label='Ángulo 2', marker='x')

	plt.title(title)
	plt.xlabel('Tiempo')
	plt.ylabel('Ángulos')
	plt.legend()
	plt.grid(True)


test_data_path = './Datos'
test_data_files_list = [file for file in os.listdir(test_data_path) if os.path.isfile(os.path.join(test_data_path, file))]

for file_name in test_data_files_list:
	print(file_name + '\n')

	file_path = os.path.join(test_data_path, file_name)
	with open(file_path) as csvfile:
		test_file_data_csvobj = csv.reader(csvfile)
		test_file_data_list = [row for row in test_file_data_csvobj]
		# print(test_file_data_list)
		# for row in test_file_data_list:
		# 	print(', '.join(row))

		# Extraer los datos que necesitamos
		
		raw_data = []
		processed_data = []
		test_file_processed_data_list = test_file_data_list[1:-2]
		
		iter = 0
		isProcesedData = False
		while iter < len(test_file_processed_data_list):
			if len(test_file_processed_data_list[iter]) != 5:
				isProcesedData = True

			if isProcesedData:
				if len(test_file_processed_data_list[iter]) == 5:
					processed_data.append(test_file_processed_data_list[iter])
			else:
				raw_data.append(test_file_processed_data_list[iter])
			
			iter += 1

		# print("Raw data")
		# print(raw_data)
		# print("\n\n")
		# print("Procesed data")
		# print(processed_data)

		plot(raw_data, 'Raw data')
		plot(processed_data, 'Processed data')
		plt.show()
	break