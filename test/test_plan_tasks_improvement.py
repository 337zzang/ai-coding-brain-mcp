import pytest
from collections import OrderedDict
from ai_helpers_new.domain.models import Plan, Task, TaskStatus
from datetime import datetime

class TestPlanTasksImprovement:
    """Plan.tasks OrderedDict 개선 테스트"""

    def test_plan_tasks_is_ordered_dict(self):
        """Plan.tasks가 OrderedDict인지 확인"""
        plan = Plan(name="Test Plan")
        assert isinstance(plan.tasks, OrderedDict)

    def test_task_order_preserved(self):
        """Task 추가 순서가 유지되는지 확인"""
        plan = Plan(name="Test Plan")

        # 3개의 Task를 순서대로 추가
        task1 = Task(id="task_1", title="First Task")
        task2 = Task(id="task_2", title="Second Task")
        task3 = Task(id="task_3", title="Third Task")

        plan.add_task(task1)
        plan.add_task(task2)
        plan.add_task(task3)

        # 순서 확인
        task_ids = list(plan.tasks.keys())
        assert task_ids == ["task_1", "task_2", "task_3"]

    def test_get_task_list(self):
        """get_task_list() 헬퍼 메서드 테스트"""
        plan = Plan(name="Test Plan")

        task1 = Task(id="task_1", title="Task 1")
        task2 = Task(id="task_2", title="Task 2")

        plan.add_task(task1)
        plan.add_task(task2)

        task_list = plan.get_task_list()
        assert isinstance(task_list, list)
        assert len(task_list) == 2
        assert task_list[0] == task1
        assert task_list[1] == task2

    def test_get_task_by_number(self):
        """get_task_by_number() 헬퍼 메서드 테스트"""
        plan = Plan(name="Test Plan")

        task1 = Task(id="task_1", title="Task 1")
        task2 = Task(id="task_2", title="Task 2")
        task3 = Task(id="task_3", title="Task 3")

        plan.add_task(task1)
        plan.add_task(task2)
        plan.add_task(task3)

        # 번호로 접근 (1부터 시작)
        assert plan.get_task_by_number(1) == task1
        assert plan.get_task_by_number(2) == task2
        assert plan.get_task_by_number(3) == task3

        # 범위 밖
        assert plan.get_task_by_number(0) is None
        assert plan.get_task_by_number(4) is None

    def test_get_task_by_id(self):
        """get_task_by_id() 헬퍼 메서드 테스트"""
        plan = Plan(name="Test Plan")

        task = Task(id="unique_id", title="Test Task")
        plan.add_task(task)

        # ID로 검색
        found_task = plan.get_task_by_id("unique_id")
        assert found_task == task

        # 존재하지 않는 ID
        assert plan.get_task_by_id("nonexistent") is None

    def test_iter_tasks(self):
        """iter_tasks() 헬퍼 메서드 테스트"""
        plan = Plan(name="Test Plan")

        tasks = [
            Task(id=f"task_{i}", title=f"Task {i}")
            for i in range(3)
        ]

        for task in tasks:
            plan.add_task(task)

        # iter_tasks()로 순회
        iterated_tasks = list(plan.iter_tasks())
        assert iterated_tasks == tasks

        # 직관적인 순회 가능
        for i, task in enumerate(plan.iter_tasks()):
            assert task == tasks[i]
            assert hasattr(task, 'status')  # AttributeError 없음

    def test_backward_compatibility(self):
        """기존 코드와의 호환성 테스트"""
        plan = Plan(name="Test Plan")

        task = Task(id="test_id", title="Test")
        plan.add_task(task)

        # 기존 방식도 여전히 작동
        assert "test_id" in plan.tasks
        assert plan.tasks["test_id"] == task

        # .items() 순회도 작동
        for task_id, task_obj in plan.tasks.items():
            assert task_id == "test_id"
            assert task_obj == task

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
