import React from 'react';
import { TodoProvider } from './contexts/TodoContext';
import TodoList from './components/TodoList';
import AddTodo from './components/AddTodo';
import styles from './styles/App.module.css';

function App() {
  return (
    <TodoProvider>
      <div className={styles.app}>
        <h1>My Todo App</h1>
        <AddTodo />
        <TodoList />
      </div>
    </TodoProvider>
  );
}

export default App;