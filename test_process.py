from multiprocessing import Process, Value, Array

def read_az(azimuth,bias):
    false_reading,angle = read_az_ang()
    if not false_reading:
        azimuth.value = (convert_az_reading(angle) - bias)%360
        print(azimuth.value)

def read_el(elevation,bias):
    false_reading,angle = read_el_ang()
    if not false_reading:
        elevation.value = angle - bias
        print(elevation.value)

if __name__ == '__main__':

    azimuth = Value('d', 0.0) # shared between processes
    elevation = Value('d', 0.0) # shared between processes

    p1 = Process(target=read_az, args=(elevation,55))
    #p2 = Process(target=read_el, args=(azimuth,bias_az))

    p1.start()
    #p2.start()

    while(1):
        print('In main')
        time.sleep(5)
