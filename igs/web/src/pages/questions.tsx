import React, { useState, useEffect } from 'react';
import backgroundImage from '../images/2.jpg';
import './questions.css';

function Questions() {
  const [step, setStep] = useState('card');
  const [answers, setAnswers] = useState({
    hasCard: '',
    travelPlan: '',
    place: '',
  });
  const [showResults, setShowResults] = useState(false);

  useEffect(() => {
    const savedStep = localStorage.getItem('quizStep');
    const savedAnswers = localStorage.getItem('quizAnswers');
    if (savedStep) setStep(savedStep);
    if (savedAnswers) setAnswers(JSON.parse(savedAnswers));
  }, []);

  const saveAnswer = (questionKey: string, value: string) => {
    const updatedAnswers = { ...answers, [questionKey]: value };
    setAnswers(updatedAnswers);
    localStorage.setItem('quizAnswers', JSON.stringify(updatedAnswers));
    
    // ЧЕТКИЕ ПУТИ БЕЗ УСЛОВИЙ
    if (questionKey === 'hasCard' && value === 'Да') {
      // Путь 1: Карта ДА -> вопрос о поездке
      setStep('travelPlan');
      localStorage.setItem('quizStep', 'travelPlan');
    }
    else if (questionKey === 'hasCard' && value === 'Нет') {
      // Путь 2: Карта НЕТ -> вопрос о месте
      setStep('place');
      localStorage.setItem('quizStep', 'place');
    }
    else if (questionKey === 'travelPlan' && value === 'Да, в лагерь') {
      // Путь 3: Поездка ДА -> РЕЗУЛЬТАТ
      setStep('result');
      localStorage.setItem('quizStep', 'result');
    }
    else if (questionKey === 'travelPlan' && value === 'Нет') {
      // Путь 4: Поездка НЕТ -> вопрос о месте
      setStep('place');
      localStorage.setItem('quizStep', 'place');
    }
    else if (questionKey === 'place' && value === 'На улице с друзьями') {
      // Путь 5: Место улица -> вопрос о поездке
      setStep('travelPlan');
      localStorage.setItem('quizStep', 'travelPlan');
    }
    else if (questionKey === 'place' && value === 'Дома') {
      // Путь 6: Место дома -> вопрос о поездке
      setStep('travelPlan');
      localStorage.setItem('quizStep', 'travelPlan');
    }
  };

  const getCurrentQuestion = () => {
    if (step === 'card') {
      return {
        text: 'Есть ли у тебя банковская карта?',
        key: 'hasCard',
        options: ['Да', 'Нет']
      };
    }
    else if (step === 'travelPlan') {
      return {
        text: 'Планируешь ли куда-то ехать в ближайшее время?',
        key: 'travelPlan',
        options: ['Да, в лагерь', 'Нет']
      };
    }
    else if (step === 'place') {
      return {
        text: 'Где ты обычно проводишь свободное время?',
        key: 'place',
        options: ['На улице с друзьями', 'Дома']
      };
    }
    else {
      return null;
    }
  };

  const currentQuestion = getCurrentQuestion();

  if (step === 'result') {
    return (
      <div style={{
        backgroundImage: `url(${backgroundImage})`,
        backgroundSize: 'cover',
        backgroundPosition: 'center',
        minHeight: '100vh',
        padding: '20px',
        color: 'black',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        textAlign: 'center'
      }}>
        <h1>Твой результат!</h1>
        <div style={{ background: 'white', padding: '20px', borderRadius: '15px', margin: '10px' }}>
          <p><strong>Банковская карта:</strong> {answers.hasCard || 'Не указано'}</p>
          <p><strong>Планы на поездку:</strong> {answers.travelPlan || 'Не указано'}</p>
          <p><strong>Где проводишь время:</strong> {answers.place || 'Не указано'}</p>
        </div>
        
        <button onClick={() => setShowResults(!showResults)} style={{ margin: '10px' }}>
          {showResults ? 'Скрыть' : 'Показать'} все сохраненные данные
        </button>
        
        {showResults && (
          <div style={{ background: 'white', padding: '20px', borderRadius: '15px', margin: '10px', maxWidth: '500px', overflow: 'auto' }}>
            <h3>Сохраненные ответы:</h3>
            <pre>{JSON.stringify(answers, null, 2)}</pre>
          </div>
        )}
        
        <button onClick={() => {
          localStorage.removeItem('quizStep');
          localStorage.removeItem('quizAnswers');
          setStep('card');
          setAnswers({
            hasCard: '',
            travelPlan: '',
            place: '',
          });
        }}>Пройти тест заново</button>
      </div>
    );
  }

  return (
    <div style={{
      backgroundImage: `url(${backgroundImage})`,
      backgroundSize: 'cover',
      backgroundPosition: 'center',
      minHeight: '100vh',
      padding: '20px',
      color: 'black',
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      justifyContent: 'center',
      textAlign: 'center'
    }}>
      <h1>Ответь на вопросы</h1>
      <p>{currentQuestion?.text}</p>
      <div>
        {currentQuestion?.options.map((option) => (
          <button
            key={option}
            onClick={() => saveAnswer(currentQuestion.key, option)}
          >
            {option}
          </button>
        ))}
      </div>
      
      <button onClick={() => setShowResults(!showResults)} style={{ marginTop: '30px', background: 'gray' }}>
        {showResults ? 'Скрыть' : 'Показать'} мои ответы
      </button>
      
      {showResults && (
        <div style={{ background: 'white', padding: '15px', borderRadius: '10px', marginTop: '20px', maxWidth: '400px' }}>
          <h4>Сохраненные ответы:</h4>
          <pre style={{ fontSize: '12px', textAlign: 'left' }}>{JSON.stringify(answers, null, 2)}</pre>
        </div>
      )}
    </div>
  );
}

export default Questions;