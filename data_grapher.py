import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import tkinter as tk
from tkinter import ttk
from tkinter import simpledialog
import numpy as np
import csv
import os

# TODO
# 1.- Be able to change between test files with a dropdown - Done
# 2.- Processed data should be generated using the raw data on the readed file - Done
# 3.- There should be controls to modify the value of the processing parameters - Done

class CustomInputDialog(tk.Toplevel):
    def __init__(self, parent, title, prompt, default_value=""):
        super().__init__(parent)
        self.result = None
        self.title(title)
        
        # Label
        tk.Label(self, text=prompt).pack(pady=10)
        
        # Large Input Field
        self.entry = tk.Entry(self, width=50)
        self.entry.insert(0, default_value)
        self.entry.pack(pady=10, padx=10)
        
        # Buttons
        button_frame = tk.Frame(self)
        button_frame.pack(pady=10)
        
        tk.Button(button_frame, text="OK", command=self.ok).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="Cancel", command=self.cancel).pack(side=tk.LEFT, padx=5)
        
        # Center the dialog
        self.geometry("+{}+{}".format(
            parent.winfo_rootx() + 50,
            parent.winfo_rooty() + 50
        ))
        
        self.transient(parent)  # Make the dialog modal
        self.grab_set()         # Block interaction with parent
        self.entry.focus_set()  # Set focus to the input field
        self.wait_window()      # Wait until the dialog is closed

    def ok(self):
        self.result = self.entry.get()
        self.destroy()

    def cancel(self):
        self.result = None
        self.destroy()


def incoherence_correction(data_angle, prev_data_angle, MAX_REAL_ANGLE_DIFFERENCE = 35):
	# MAX_REAL_ANGLE_DIFFERENCE = 35	# The maximum possible angles difference between frames 
	CORRECTION_CONSTANT = MAX_REAL_ANGLE_DIFFERENCE * MAX_REAL_ANGLE_DIFFERENCE # A constant to calculate the correction value used to correct irregular differences 
	discrepancy = 0

	angle_difference = abs(data_angle - prev_data_angle)
	if angle_difference > MAX_REAL_ANGLE_DIFFERENCE: # If the increment in a single frame is realistically impossible...
		correction = data_angle - ( prev_data_angle + (CORRECTION_CONSTANT / angle_difference) ) # Generate the correction value based on the previous data
		data_angle = data_angle - correction # Fix the value with the generated correction
		discrepancy += 1

	return data_angle, discrepancy


def nonlinear_correction(data_angle, prev_data_angle, frame_index, frames_data_filtered, ASSUMED_MIN_FRAME_MOVEMENT = 5):	# The minimum angle movement between frames 
	discrepancy = 0

	data_angle = float(data_angle)
	prev_data_angle = float(prev_data_angle)
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
	frames_data_filtered_as_string = ""
	for data in frames_data_filtered:
		# Turn data into a string
		frames_data_filtered_as_string += f"{data[0]}, {data[1]}, {data[2]}, {data[3]}, {data[4]}\n"
	
	return frames_data_filtered_as_string


def data_postprocess(frames_data_list, config):
	discrepancies_counter = 0 # Counts the times some data had to be corrected  
	frames_data_filtered = [] # New list for filtered data

	for i in range(0, len(frames_data_list)):
		data = frames_data_list[i] # The actual frame
		data_angle1 = data[0] # Motor angle
		data_angle2 = data[1] # Arrow angle
		TIMESTAMP = data[4]

		if i == 0: # If its the first frame...
			# Make the first frame always be on angle 0
			data_angle1 = 0
			data_angle2 = 0
		else:
			prev_data = frames_data_filtered[i - 1] # Get the data of the previous frame from the filtered data
			prev_data_angle1 = prev_data[0]
			prev_data_angle2 = prev_data[1]

			# NON-LINEAR DATA CORRECTION
			data_angle1, discrepancy1 = nonlinear_correction(data_angle1, prev_data_angle1, i, frames_data_filtered, config["assumed_min_frame_movement"])
			data_angle2, discrepancy2 = nonlinear_correction(data_angle2, prev_data_angle2, i, frames_data_filtered, config["assumed_min_frame_movement"])

			# INCOHERENT INCREMENT CORRECTION
			data_angle1, discrepancy3 = incoherence_correction(data_angle1, prev_data_angle1, config["max_real_angle_difference"])
			data_angle2, discrepancy4 = incoherence_correction(data_angle2, prev_data_angle2, config["max_real_angle_difference"])
			
			discrepancies_counter += (discrepancy1 + discrepancy2 + discrepancy3 + discrepancy4)

		# Calculate the new difference between the filtered angles
		filtered_angles_diference_brute = data_angle2 - data_angle1
		filtered_angles_diference = (filtered_angles_diference_brute + 180) % 360 - 180
		filtered_angles_diference = round(abs(filtered_angles_diference), 3) # Apply rounding at 3 decimals and make it absolute

		# Add filtered data to the new list
		frames_data_filtered.append([round(data_angle1, 3), round(data_angle2,3) , data[2], filtered_angles_diference, TIMESTAMP])

	print(f"Discrepancies: {discrepancies_counter}\n")
	
	return frames_data_filtered


def analizePostprocessedData(filtered_frames_data, config):
	# Purge system from previuous angle analysis
	test_error_status = ""
	is_test_result = True

	filtered_desync_start = False
	filtered_desync_start_time = 0
	filtered_desync_time = 0

	error_max_angle_filtered = False
	error_max_time_filtered = False

	for frame in filtered_frames_data:
		filtered_angles_diference = frame[3]
		TIMESTAMP = float(frame[4])

		if filtered_angles_diference > config["max_angle_difference"]:
			is_test_result = False
			if not error_max_angle_filtered:
				test_error_status += "$max_angle_diff"
			error_max_angle_filtered = True

		if filtered_angles_diference > config["valid_threshold"]:
			if not filtered_desync_start:
				filtered_desync_start_time = TIMESTAMP
			
			filtered_desync_start = True
		else:
			filtered_desync_start = False
			 

		if filtered_desync_start:
			filtered_desync_time = TIMESTAMP - filtered_desync_start_time
			# desync_time = round(frame_loop_endtime, 3) - round(desync_start, 3)
			if filtered_desync_time > config["max_desync_time"]:
				is_test_result = False
				if not error_max_time_filtered:
					test_error_status += "$max_desync_time"
				error_max_time_filtered = True
	
	return is_test_result, test_error_status


def plot(data_array, title, graph, isString = True):
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
	global last_file_name, current_is_test_passed, current_test_status, current_raw_data, current_processed_data
	input_values = get_text_field_values()

	config = {
		"valid_threshold": input_values[0],
		"max_angle_difference": input_values[1],
		"max_desync_time": input_values[2],
		"assumed_min_frame_movement": input_values[3],
		"max_real_angle_difference": input_values[4],

	}

	file_name = file_selector.get()
	if (file_name != last_file_name):
		reset_text_field_values()
	last_file_name = file_name
	file_path = os.path.join(test_data_path, file_name)
	with open(file_path) as csvfile:
		test_file_data_csvobj = csv.reader(csvfile)
		test_file_data_list = [row for row in test_file_data_csvobj]

		# Extract needed data		
		raw_data = []
		processed_data = []

		# Get the data only
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

	calculated_processed_data = data_postprocess(raw_data, config)
	is_test_passed, test_status = analizePostprocessedData(calculated_processed_data, config)
	update_test_status(is_test_passed, test_status)

	# Save the current status for further use
	current_is_test_passed = is_test_passed
	current_test_status = test_status


	# Graph again with new data
	plot(raw_data, 'Datos en crudo', raw_graph)
	plot(calculated_processed_data, 'Datos postprocesados', processed_graph, False)

	# Redraw graphs
	canvas.draw()

	# Save the current data for further use
	current_raw_data = raw_data
	current_processed_data = processed_data


# Function to prompt the user for a string
def prompt_file_title(parent):
    dialog = CustomInputDialog(parent, "Guardar archivo", "Nombre del archivo:", default_value=file_selector.get())
    if dialog.result is not None:
        return True, dialog.result
    else:
        return False, dialog.result

def generate_data_file():
	global last_file_name, current_is_test_passed, current_test_status, current_raw_data, current_processed_data

	is_file_name_received, new_file_name = prompt_file_title(root)
	if is_file_name_received:
		print(f'File name: {new_file_name}')
		
		raw_data_string = frame_data_to_string(current_raw_data)
		processed_data_string = frame_data_to_string(current_processed_data)
		row_number = raw_data_string.count('\n') + processed_data_string.count('\n')
		file_head = f'result, {'PASS' if current_is_test_passed else 'FAIL'}, failure_motive, {current_test_status}, cols, 5, rows, {row_number}\n'
		file_tail = ',EOF\n'

		file_content = file_head + raw_data_string + '\n' + processed_data_string + file_tail
		print('File content: \n' + file_content)
		with open(new_file_name, "w") as file:
			file.write(file_content)


def update_test_status(is_test_passed, test_status: str):
	if is_test_passed:
		status_text.set("Con esta configuración la prueba: Pasa")
	else:
		status_text.set(f"Con esta configuración la prueba: Falla con el codigo de error: {test_status}")


def get_text_field_values():
	values = [float(field.get()) for field in text_fields]
	return values

def reset_text_field_values():
	for i in range(5):
		text_fields[i].delete(0, tk.END)
		text_fields[i].insert(0, tags[i]['default'])


def close_program():
	root.quit()
	root.destroy()

global last_file_name, current_is_test_passed, current_test_status, current_raw_data, current_processed_data
last_file_name = ""
current_is_test_passed = True
current_test_status = ""
current_raw_data = []
current_processed_data = []

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
file_selector = ttk.Combobox(frame_controls, values=test_data_files_list, state="readonly", width=50)
file_selector.set(test_data_files_list[0])  # Set default value
file_selector.pack(side=tk.LEFT, padx=5)

# Button to update the graphs
btn_update = ttk.Button(root, text='Actualizar Gráfica', command=update_graphs)
btn_update.pack(side=tk.LEFT, padx=10, pady=10)

# Button to save file
btn_save = ttk.Button(root, text="Guardar en archivo", command=generate_data_file)
btn_save.pack(side=tk.LEFT, padx=10, pady=10)

# Create a frame for the text fields
frame_text_fields = tk.Frame(root)
frame_text_fields.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=10)

# Labels and Entry widgets
text_field_labels = []
text_fields = []
tags = [
	{"name": "Diferencia minima", "default": 35}, # Valid threshold
	{"name": "Diferencia maxima", "default": 70}, # max angle difference
	{"name": "Tiempo maximo de desinc.", "default": 5}, # max desync time
	{"name": "Movimiento minimo", "default": 5}, # ASSUMED_MIN_FRAME_MOVEMENT
	{"name": "Maxima diferencia real", "default": 35}, # MAX_REAL_ANGLE_DIFFERENCE
]

for i in range(5):
	label = ttk.Label(frame_text_fields, text=f"{tags[i]["name"]}:")
	label.pack(side=tk.LEFT, padx=5)
	text_field_labels.append(label)

	entry = ttk.Entry(frame_text_fields, width=10)
	entry.insert(0, tags[i]["default"])
	entry.pack(side=tk.LEFT, padx=5)
	text_fields.append(entry)


# Create a StringVar for the label text
status_text = tk.StringVar()
status_text.set("Ready")  # Set an initial value

# Create the Label and bind it to the StringVar
status_label = ttk.Label(root, textvariable=status_text)
status_label.pack(side=tk.BOTTOM, pady=10)	

# Allow easy program closing
root.protocol("WM_DELETE_WINDOW", close_program)

# Executed once before the app runs to ensure the graphs have data on them from start
update_graphs()

root.mainloop()