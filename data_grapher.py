import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import tkinter as tk
from tkinter import ttk
import numpy as np
import csv
import os

# TODO
# 1.- Be able to change between test files with a dropdown - Done
# 2.- Processed data should be generated using the raw data on the readed file
# 3.- There should be controls to modify the value of the processing parameters

def plot(data_array, title, graph):
	eje_x = np.array([float(row[4].strip()) for row in data_array])  # Get Time
	angulo_1 = np.array([float(row[0].strip()) for row in data_array])  # Get Motor angle
	angulo_2 = np.array([float(row[1].strip()) for row in data_array])  # Get arrow angle

	# Update graph
	graph.plot(eje_x, angulo_1, label='Ángulo 1', marker='o')
	graph.plot(eje_x, angulo_2, label='Ángulo 2', marker='x')
	graph.set_title(title)
	graph.set_xlabel('Tiempo')
	graph.set_ylabel('Ángulos')
	graph.legend()
	graph.grid(True)


def update_graphs():
	file_name = file_selector.get()
	file_path = os.path.join(test_data_path, file_name)
	with open(file_path) as csvfile:
		test_file_data_csvobj = csv.reader(csvfile)
		test_file_data_list = [row for row in test_file_data_csvobj]

		# Extract needed data		
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
	
	# Delete previous graphs
	raw_graph.clear()
	processed_graph.clear()

	# Graph again with new data
	plot(raw_data, 'Raw data', raw_graph)
	plot(processed_data, 'Processed data', processed_graph)

	# Redraw graphs
	canvas.draw()


def close_program():
    root.quit()
    root.destroy()


test_data_path = './Datos'
test_data_files_list = [file for file in os.listdir(test_data_path) if os.path.isfile(os.path.join(test_data_path, file))]

root = tk.Tk()
root.title('Visualizador de datos procesados')
fig, (raw_graph, processed_graph) = plt.subplots(2, 1, figsize=(10, 8))
fig.tight_layout(pad=5)

# Add Matplotlib figure to the interface
canvas = FigureCanvasTkAgg(fig, master=root)
canvas_widget = canvas.get_tk_widget()
canvas_widget.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

# Controls
frame_controls = tk.Frame(root)
frame_controls.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=10)


# Dropdown for selecting files
file_selector_label = ttk.Label(frame_controls, text="Select File:")
file_selector_label.pack(side=tk.LEFT, padx=5)
file_selector = ttk.Combobox(frame_controls, values=test_data_files_list, state="readonly")
file_selector.set(test_data_files_list[0])  # Set default value
file_selector.pack(side=tk.LEFT, padx=5)

# Button to update the graphs
btn_update = ttk.Button(root, text='Actualizar Gráfica', command=update_graphs)
btn_update.pack(side=tk.LEFT, padx=10, pady=10)

root.protocol("WM_DELETE_WINDOW", close_program)

# Executed once before the app runs to ensure the graphs have data on them from start
update_graphs()

root.mainloop()