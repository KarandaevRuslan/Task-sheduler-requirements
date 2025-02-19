from typing import List

class Task:
    def __init__(self, id, deadline, duration, priority, status, dependencies=None):
        """
        :param id: уникальный идентификатор задачи
        :param deadline: дедлайн задачи (например, целое число или timestamp)
        :param duration: оценочное время выполнения задачи
        :param priority: приоритет (1..5), 5 – самый высокий
        :param status: статус ("К выполнению", "выполняется", "на паузе", "отменено", "выполнено", "удалено")
        :param dependencies: список id задач, которые должны быть выполнены ДО этой
        """
        self.id = id
        self.deadline = deadline
        self.duration = duration
        self.priority = priority
        self.status = status
        self.dependencies = dependencies if dependencies else []
        self.start_time = None
        self.finish_time = None

    def __repr__(self):
        return (f"Task(id={self.id}, deadline={self.deadline}, duration={self.duration}, "
                f"priority={self.priority}, status={self.status}, "
                f"start={self.start_time}, finish={self.finish_time})")


def topological_sort_with_priority(tasks: List[Task], alpha=1.0) -> List[Task]:
    """
    Топологическая сортировка с учётом «эффективного дедлайна», чтобы при одинаковом
    уровне зависимостей раньше шли задачи с меньшим effective_deadline.

    effective_deadline = deadline - alpha * priority
    (приоритет 5 даёт более сильное «сокращение» дедлайна, чем приоритет 1)
    """
    # Создаём словарь для быстрого доступа по id
    task_map = {t.id: t for t in tasks}

    # Считаем "in_degree" (количество зависимостей) и строим граф
    in_degree = {t.id: 0 for t in tasks}
    graph = {t.id: [] for t in tasks}

    for t in tasks:
        for dep_id in t.dependencies:
            if dep_id in task_map:
                graph[dep_id].append(t.id)
                in_degree[t.id] += 1

    # Подготовим структуру для "очереди" задач без зависимостей
    # Будем держать их упорядоченными по возрастанию effective_deadline
    def effective_deadline(task):
        return task.deadline - alpha * task.priority

    zero_in_degree = [t for t in tasks if in_degree[t.id] == 0]
    zero_in_degree.sort(key=effective_deadline)

    sorted_list = []

    # Алгоритм Кана, но с учётом сортировки по effective_deadline
    while zero_in_degree:
        current = zero_in_degree.pop(0)
        sorted_list.append(current)

        for nbr_id in graph[current.id]:
            in_degree[nbr_id] -= 1
            if in_degree[nbr_id] == 0:
                zero_in_degree.append(task_map[nbr_id])
        # Пересортируем по effective_deadline
        zero_in_degree.sort(key=effective_deadline)

    # Проверяем, все ли попали в итоговый список
    if len(sorted_list) != len(tasks):
        raise Exception("Существует циклическая зависимость между задачами!")

    return sorted_list


def schedule_tasks_with_priority(tasks: List[Task], alpha=1.0) -> List[Task]:
    """
    Планирование задач "вправо" с учётом приоритета.
    :param tasks: список задач
    :param alpha: коэффициент, определяющий силу влияния приоритета
    :return: список задач (та же ссылка), где заполнены start_time и finish_time
    """

    # 1. Фильтрация по статусу
    valid_statuses = {"К выполнению", "выполняется", "на паузе"}
    tasks_to_do = [t for t in tasks if t.status in valid_statuses]

    if not tasks_to_do:
        return []

    # 2. Топологическая сортировка (учитывает зависимости + приоритет через effective_deadline)
    tasks_ordered = topological_sort_with_priority(tasks_to_do, alpha=alpha)

    # 3. Определим, как будем планировать "вправо":
    #    Возьмём максимальный реальный дедлайн среди задач
    max_deadline = max(t.deadline for t in tasks_ordered)
    current_time = max_deadline

    # Ставим задачи в обратном порядке (чтобы каждая задача была как можно ближе к своему дедлайну)
    # Обратите внимание, что tasks_ordered у нас уже "топологически" упорядочен,
    # но теперь мы идём с конца этого списка, чтобы сдвинуть "вправо".
    for t in reversed(tasks_ordered):
        # Задаём finish_time: это минимум из "текущего времени" и "реального дедлайна"
        finish = min(current_time, t.deadline)
        start = finish - t.duration

        # Проставляем времена
        t.finish_time = finish
        t.start_time = start

        # Передвигаем "указатель" влево для предыдущих задач
        current_time = start

    return tasks_ordered


# Пример использования
if __name__ == "__main__":
    # Допустим, есть 6 задач:
    raw_tasks = [
        Task(id=1, deadline=50,  duration=10, priority=3, status="К выполнению"),   # дедлайн 50, приоритет 3
        Task(id=2, deadline=55,  duration=5,  priority=5, status="выполняется"),    # дедлайн 55, приоритет 5
        Task(id=3, deadline=60,  duration=5,  priority=2, status="К выполнению"),   # дедлайн 60, приоритет 2
        Task(id=4, deadline=60,  duration=10, priority=4, status="на паузе"),       # дедлайн 60, приоритет 4
        Task(id=5, deadline=100, duration=5,  priority=1, status="отменено"),       # это не пойдёт в план
        Task(id=6, deadline=70,  duration=5,  priority=3, status="К выполнению", dependencies=[4,1]),
    ]

    # Прогоним планировщик с разными alpha
    # 1) alpha = 0 (приоритет отключён, порядок строго по дедлайнам)
    # 2) alpha = 5 (приоритет максимально сильно влияет на относительный порядок)
    for test_alpha in [0, 5]:
        print(f"\n=== ПЛАНИРОВАНИЕ ПРИ alpha={test_alpha} ===")
        scheduled = schedule_tasks_with_priority(raw_tasks, alpha=test_alpha)
        for s in scheduled:
            print(s)
