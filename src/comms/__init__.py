from concurrent.futures import ThreadPoolExecutor


def run_tasks_in_parallel(tasks) -> None:
    """
    Start each function running in parallel and then wait until they finish.
    Yes, this function will block until they are all done
    :param tasks: A list of function objects to run
    :return: None. It would be nice to return the results but how to associate a given
    result with the task that produced it? That would require a bit more infrastructure
    than I want to add at this time.
    """
    with ThreadPoolExecutor() as executor:
        running_tasks = [executor.submit(task) for task in tasks]
        for running_task in running_tasks:
            running_task.result()

