from actors.Simulation import Simulation
import settings as s
from actors.Task import Status
from dispatch_tasks import send_task_request_to_task_assigner_async, send_task_data_to_cloud


def handle_tasks():
    if Simulation.current_time < s.TASK_GENERATION_START_TIME:
        return
    new_tasks = Simulation.task_generator.generate_new_tasks(Simulation.current_time)
    for task in new_tasks:
        Simulation.tasks.append(task)
        send_task_request_to_task_assigner_async(Simulation.task_assigner_host_ip, task)
        Simulation.task_organizer.add_task(Simulation.current_time, task)
    Simulation.task_organizer.handle_tasks(Simulation.current_time)
