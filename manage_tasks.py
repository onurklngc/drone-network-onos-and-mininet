import settings as s
from actors.Record import TaskRecord
from actors.Simulation import Simulation
from dispatch_tasks import send_task_request_to_task_assigner_async


def handle_tasks():
    if Simulation.current_time < s.TASK_GENERATION_START_TIME:
        return
    new_tasks = Simulation.task_generator.generate_new_tasks(Simulation.current_time)
    for task in new_tasks:
        task_record = TaskRecord(task.no, task.start_time, task.owner.sumo_id, task.priority, task.size, task.deadline)
        Simulation.record.tasks[task.no] = task_record
        Simulation.tasks.append(task)
        send_task_request_to_task_assigner_async(Simulation.task_assigner_host_ip, task)
        Simulation.task_organizer.add_task(Simulation.current_time, task)
    Simulation.task_organizer.handle_tasks(Simulation.current_time)
