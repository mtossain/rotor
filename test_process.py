
def read_sensor():

    global conf,stat

    if az_sense_active:
        state.az_false_reading,angle = read_az_ang() # Read azimuth sensor output
        if not state.az_false_reading:
            state.az_rep = (convert_az_reading(angle) - conf.bias_az)%360 # Convert for AMS5048 readings

    if el_sense_active:
        state.el_false_reading,angle = read_el_ang()
        if not state.el_false_reading:
            state.el_rep = angle - conf.bias_el # Read elevation sensor output
