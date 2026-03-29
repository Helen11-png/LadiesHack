import React from 'react';
import logo from './logo.svg';
import TextInput from 'react'
import './App.css';

function App() {
  return (
    <div className="App">
      <header className="App-header">
        <h1>
          Какой ты человек, исходя из квиза по страхованию??
        </h1>
        <p>
          Страхование — это инструмент защиты от финансовых потерь, которые возможны в определенных случаях
        </p>
        <p>
          Собери своего персонажа:
        </p>
        <p>Введи имя своего персонажа:</p>
        <input name="myInput" />
        <p>Выберите свой возраст:</p>
        <div>
        <button>младше 11</button>
        <button>11-12</button>
        <button>13-14</button>
        <button>15-16</button>
        <button>17-18</button>
        <button>Старше 18</button>
        </div>
        <p>Выберите свой пол:</p>
        <div>
        <button>Ж</button>
        <button>М</button>
        </div>
        <button>НАЧАТЬ ТЕСТ</button>
      </header>
    </div>
  );
}

export default App;
