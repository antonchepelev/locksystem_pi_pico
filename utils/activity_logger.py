
import utime

def get_date_and_time():
    current_time = utime.time()

    local_time = utime.localtime(current_time)

    year, month, day, hour, minute, second = local_time[:6]
    
    
    date = f'{month}-{day}-{str(year)[2:]}'
    
    time = f'{hour}:{minute}:{second}'
    
    return date, time
    
    


def activity_logger(status):
    """ 
    Log activity to a CSV file.

    Parameters:
    - status (str): The status to be logged.
    
    """
    
    status = status
    
    date , time = get_date_and_time()

    
    with open("lock_system_activity_log.csv", 'a') as file:
        
        file.write(f"\n{status},{date},{time},")

