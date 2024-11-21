import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import tkinter as tk
from tkinter import ttk
import numpy as np
import csv
import os

# TODO
# 1.- Be able to change between test files with a dropdown - Done
# 2.- Processed data should be generated using the raw data on the readed file - Done
# 3.- There should be controls to modify the value of the processing parameters

def incoherence_correction(data_angle, prev_data_angle):
	MAX_REAL_ANGLE_DIFFERENCE = 35	# The maximum possible angles difference between frames 
	CORRECTION_CONSTANT = MAX_REAL_ANGLE_DIFFERENCE * MAX_REAL_ANGLE_DIFFERENCE # A constant to calculate the correction value used to correct irregular differences 
	discrepancy = 0

	angle_difference = abs(data_angle - prev_data_angle)
	if angle_difference > MAX_REAL_ANGLE_DIFFERENCE: # If the increment in a single frame is realistically impossible...
		correction = data_angle - ( prev_data_angle + (CORRECTION_CONSTANT / angle_difference) ) # Generate the correction value based on the previous data
		data_angle = data_angle - correction # Fix the value with the generated correction
		discrepancy += 1

	return data_angle, discrepancy


def nonlinear_correction(data_angle, prev_data_angle, frame_index, frames_data_filtered):
	ASSUMED_MIN_FRAME_MOVEMENT = 5	# The minimum angle movement between frames 
	discrepancy = 0

	data_angle = float(data_angle)
	prev_data_angle = float(prev_data_angle)
	# print(f'DATA ANGLE: {type(data_angle)} - {data_angle}')
	# print(f'PREV DATA ANGLE: {type(prev_data_angle)} - {prev_data_angle}')
	if data_angle < prev_data_angle: # If theres non-linear data...
		# Make it make sense:
		is_normal_detection_issue = False # If its not a special case, do the normal fix

		if frame_index > 4 and (data_angle < 300): # If theres enough data to make an assumption and the angle is between 0 and 299...
			data_average = (frames_data_filtered[frame_index-1][0] + frames_data_filtered[frame_index-2][0] + frames_data_filtered[frame_index-3][0]) / 3 # Get the average angle of the last 3 frames 
			if data_average > 300: # If we are close to the full lap...
				# Assume that we are passing the 360 degrees limit
				data_angle = 360 + data_angle
			else:
				# Assume that a detection issue happended
				is_normal_detection_issue = True
		else:
			# Assume that a detection issue happended
			is_normal_detection_issue = True

		if is_normal_detection_issue:
			while (data_angle < prev_data_angle):
				data_angle = data_angle + ASSUMED_MIN_FRAME_MOVEMENT

			discrepancy += 1
	
	return data_angle, discrepancy


def frame_data_to_string(frames_data_filtered):
	print("\nDEBUG FILTER RESULT:")
	frames_data_filtered_as_string = ""
	for data in frames_data_filtered:
		# Turn data into a string
		# print(data)
		frames_data_filtered_as_string += f"{data[0]}, {data[1]}, {data[2]}, {data[3]}, {data[4]}\n"
	
	return frames_data_filtered_as_string

def data_postprocess(frames_data_list):
	discrepancies_counter = 0 # Counts the times some data had to be corrected  
	frames_data_filtered = [] # New list for filtered data

	# print("DEBUG TEST DATA FILTERING")
	for i in range(0, len(frames_data_list)):
		data = frames_data_list[i] # The actual frame
		data_angle1 = data[0] # Motor angle
		data_angle2 = data[1] # Arrow angle
		TIMESTAMP = data[4]

		#print(data) # Debug: Show raw data of every frame

		if i == 0: # If its the first frame...
			# Make the first frame always be on angle 0
			data_angle1 = 0
			data_angle2 = 0
		else:
			prev_data = frames_data_filtered[i - 1] # Get the data of the previous frame from the filtered data
			prev_data_angle1 = prev_data[0]
			prev_data_angle2 = prev_data[1]

			# NON-LINEAR DATA CORRECTION
			data_angle1, discrepancy1 = nonlinear_correction(data_angle1, prev_data_angle1, i, frames_data_filtered)
			data_angle2, discrepancy2 = nonlinear_correction(data_angle2, prev_data_angle2, i, frames_data_filtered)

			# INCOHERENT INCREMENT CORRECTION
			data_angle1, discrepancy3 = incoherence_correction(data_angle1, prev_data_angle1)
			data_angle2, discrepancy4 = incoherence_correction(data_angle2, prev_data_angle2)
			
			discrepancies_counter += (discrepancy1 + discrepancy2 + discrepancy3 + discrepancy4)

		# Calculate the new difference between the filtered angles
		filtered_angles_diference_brute = data_angle2 - data_angle1
		filtered_angles_diference = (filtered_angles_diference_brute + 180) % 360 - 180
		filtered_angles_diference = round(abs(filtered_angles_diference), 3) # Apply rounding at 3 decimals and make it absolute

		# Add filtered data to the new list
		frames_data_filtered.append([round(data_angle1, 3), round(data_angle2,3) , data[2], filtered_angles_diference, TIMESTAMP])

	print(f"Discrepancies: {discrepancies_counter}\n")
	
	return frames_data_filtered

# filtered_frames_data = data_postprocess(frames_data_list)
# analizePostprocessedData(filtered_frames_data)
# filtered_frames_data_string = frame_data_to_string(filtered_frames_data)

def analizePostprocessedData(filtered_frames_data):
	# global valid_threshold, max_angle_difference, max_desync_time, global_test_result, global_test_error_status
	# Purge system from previuous angle analysis
	global_test_error_status = ""
	global_test_result = True

	filtered_desync_start = False
	filtered_desync_start_time = 0
	filtered_desync_time = 0

	error_max_angle_filtered = False
	error_max_time_filtered = False

	for frame in filtered_frames_data:
		filtered_angles_diference = frame[3]
		TIMESTAMP = frame[4]

		if filtered_angles_diference > max_angle_difference:
			print(f"MAX ANGLE DIF: {angle_diference}")
			global_test_result = False
			if not error_max_angle_filtered:
				global_test_error_status += "$max_angle_diff"
			error_max_angle_filtered = True

		if filtered_angles_diference > valid_threshold:
			if not filtered_desync_start:
				filtered_desync_start_time = TIMESTAMP
			
			filtered_desync_start = True
		else:
			filtered_desync_start = False
			 

		if filtered_desync_start:
			filtered_desync_time = TIMESTAMP - filtered_desync_start_time
			# desync_time = round(frame_loop_endtime, 3) - round(desync_start, 3)
			if filtered_desync_time > max_desync_time:
				global_test_result = False
				if not error_max_time_filtered:
					global_test_error_status += "$max_desync_time"
				error_max_time_filtered = True



def plot(data_array, title, graph, isString = True):
	print(data_array)
	eje_x = np.array([float(row[4].strip()) for row in data_array]) # Get Time
	angulo_1 = np.array([(float(row[0].strip()) if isString else row[0]) for row in data_array])  # Get Motor angle
	angulo_2 = np.array([(float(row[1].strip()) if isString else row[1]) for row in data_array])  # Get arrow angle

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
		test_file_processed_data_list = test_file_data_list[1:-1]
		
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


	# print('raw DATA:')
	# for data in raw_data:
	# 	print(data)

	# Calculate processed data:
	calculated_processed_data = data_postprocess(raw_data)
	# print('GENERATED PROCESSED DATA:')
	# for data in calculated_processed_data:
	# 	print(data)

	# print('\n')
	# print('PROCESSED DATA from file:')
	# for data in processed_data:
	# 	print(data)



	# Graph again with new data
	plot(raw_data, 'Raw data', raw_graph)
	plot(calculated_processed_data, 'Processed data', processed_graph, False)

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
file_selector_label = ttk.Label(frame_controls, text="Archivo:")
file_selector_label.pack(side=tk.LEFT, padx=5)
file_selector = ttk.Combobox(frame_controls, values=test_data_files_list, state="readonly")
file_selector.set(test_data_files_list[0])  # Set default value
file_selector.pack(side=tk.LEFT, padx=5)

# Button to update the graphs
btn_update = ttk.Button(root, text='Actualizar Gráfica', command=update_graphs)
btn_update.pack(side=tk.LEFT, padx=10, pady=10)





# Create a frame for the text fields
frame_text_fields = tk.Frame(root)
frame_text_fields.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=10)

# Labels and Entry widgets for 5 numbers
text_field_labels = []
text_fields = []

tags = [
	# valid_threshold = 35
	# max_angle_difference = 70
	# max_desync_time = 5
	# test_delay = 0
	{"name": "Diferencia minima", "default": 35}, # Valid threshold
	{"name": "Diferencia maxima", "default": 70}, # max angle difference
	{"name": "Tiempo maximo de desinc.", "default": 5}, # max desync time
	{"name": "Movimiento minimo", "default": 5}, # ASSUMED_MIN_FRAME_MOVEMENT
	{"name": "Maxima diferencia real", "default": 35}, # MAX_REAL_ANGLE_DIFFERENCE
]
for i in range(5):
	print(i)
	label = ttk.Label(frame_text_fields, text=f"{tags[i]["name"]}:")
	label.pack(side=tk.LEFT, padx=5)
	text_field_labels.append(label)

	entry = ttk.Entry(frame_text_fields, width=10)
	entry.insert(0, tags[i]["default"])
	entry.pack(side=tk.LEFT, padx=5)
	text_fields.append(entry)

# Example: Accessing the entered values
def get_text_field_values():
	values = [field.get() for field in text_fields]
	print(f"Entered values: {values}")
	return values






root.protocol("WM_DELETE_WINDOW", close_program)

# Executed once before the app runs to ensure the graphs have data on them from start
update_graphs()

root.mainloop()