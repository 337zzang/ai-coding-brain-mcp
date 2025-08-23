// Todo App JavaScript
let todos = [];

function addTodo() {
    const input = document.getElementById('todoInput');
    if (input.value.trim()) {
        todos.push({
            id: Date.now(),
            text: input.value,
            completed: false
        });
        input.value = '';
        renderTodos();
    }
}

function renderTodos() {
    const list = document.getElementById('todoList');
    list.innerHTML = todos.map(todo => 
        `<li>${todo.text}</li>`
    ).join('');
}