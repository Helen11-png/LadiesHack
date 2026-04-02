import React, { useState } from 'react';
import backgroundImage from '../images/1.jpg';
import { useNavigate } from 'react-router-dom';
import './home.css';

function Home() {
  const navigate = useNavigate();
  const [ageGroup, setAgeGroup] = useState('');
  const [gender, setGender] = useState('');
  const handleStartTest = () => {
    navigate('/questions'); // переход на страницу /quiz
  };
  const saveData = (key: string, value: string) => {
    const data = { ageGroup, gender };
    const updatedData = { ...data, [key]: value };
    localStorage.setItem('quizData', JSON.stringify(updatedData));
  };

  const handleAgeSelect = (age: string) => {
    setAgeGroup(age);
    saveData('ageGroup', age);
  };

  const handleGenderSelect = (g: string) => {
    setGender(g);
    saveData('gender', g);
  };

  return (
    <div style={{
      backgroundImage: `url(${backgroundImage})`,
      backgroundSize: 'cover',
      backgroundPosition: 'center',
      minHeight: '100vh',
      padding: '20px',
      color: 'white'
    }}>
      <h1>Какой ты человек, </h1>
      <h1>исходя из квиза по страхованию??</h1>
      <p>
          Собери своего персонажа:
        </p>
        <p>Введи имя своего персонажа:</p>
        <input name="myInput" />
        <p>Выберите свой возраст:</p>
        <div>
        <button 
          className={ageGroup === 'младше 11' ? 'active' : ''}
          onClick={() => handleAgeSelect('младше 11')}
        >младше 11</button>
        <button 
          className={ageGroup === '11-12' ? 'active' : ''}
          onClick={() => handleAgeSelect('11-12')}
        >11-12</button>
        <button 
          className={ageGroup === '13-14' ? 'active' : ''}
          onClick={() => handleAgeSelect('13-14')}
        >13-14</button>
        <button 
          className={ageGroup === '15-16' ? 'active' : ''}
          onClick={() => handleAgeSelect('15-16')}
        >15-16</button>
        <button 
          className={ageGroup === '17-18' ? 'active' : ''}
          onClick={() => handleAgeSelect('17-18')}
        >17-18</button>
        <button 
          className={ageGroup === 'Старше 18' ? 'active' : ''}
          onClick={() => handleAgeSelect('Старше 18')}
        >Старше 18</button>
        </div>
        <p>Выберите свой пол:</p>
        <div>
        <button 
          className={gender === 'Ж' ? 'active' : ''}
          onClick={() => handleGenderSelect('Ж')}
        >Ж</button>
        <button 
          className={gender === 'М' ? 'active' : ''}
          onClick={() => handleGenderSelect('М')}
        >М</button>
        </div>
        <button className="start-button" onClick={handleStartTest}>
      НАЧАТЬ ТЕСТ
    </button>
    </div>
  );
}

export default Home;