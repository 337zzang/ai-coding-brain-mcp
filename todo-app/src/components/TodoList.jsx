import React, { useContext } from 'react';
import { TodoContext } from '../contexts/TodoContext';
import TodoItem from './TodoItem';
import styles from '../styles/Todo.module.css';

const TodoList = () => {
  const { todos } = useContext(TodoContext);

  return (
    <div className={styles.todoList}>
      {todos.length === 0 ? (
        <p className={styles.emptyMessage}>No todos yet. Add one!</p>
      ) : (
        todos.map(todo => <TodoItem key={todo.id} todo={todo} />)
      )}
    </div>
  );
};

export default TodoList;