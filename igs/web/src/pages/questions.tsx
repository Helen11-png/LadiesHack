import React, { useState } from 'react';
import backgroundImage from '../images/2.jpg';
import './questions.css';

function Questions() {
  const [step, setStep] = useState(0); // какой вопрос сейчас показываем
  const [answers, setAnswers] = useState({
    hasCard: '',
    travelling: '',
    freetime: '',
  });

  const saveAnswer = (questionKey: string, value: string) => {
    const updatedAnswers = { ...answers, [questionKey]: value };
    setAnswers(updatedAnswers);
    localStorage.setItem('quizAnswers', JSON.stringify(updatedAnswers));
    
    // ЛОГИКА РАЗВЕТВЛЕНИЙ
    // Переход к следующему вопросу в зависимости от ответа
    if (questionKey === 'hasCard') {
      if (value === 'да') {
        setStep(1); // следующий вопрос
      } else {
        setStep(3); // пропускаем к другому вопросу или финалу
      }
    } else if (questionKey === 'travelling') {
      if (value === 'да') {
        setStep(2);
      } else {
        setStep(3);
      }
    } else if (questionKey === 'freetime') {
      setStep(4); // конец теста
    }
  };

  const getCurrentQuestion = () => {
    switch(step) {
      case 0:
        return {
          text: 'Есть ли у тебя банковская карта?',
          key: 'hasCard'
        };
      case 1:
        return {
          text: 'Планируешь ли куда-то ехать в ближайшее время?',
          key: 'travelling'
        };
      case 2:
        return {
          text: 'Где ты обычно проводишь свободное время?',
          key: 'freetime'
        };
      case 3:
        return {
          text: 'Как ты обычно отдыхаешь?',
          key: 'restType'
        };
      case 4:
        return {
          text: 'Спасибо за ответы!',
          key: 'finish'
        };
      default:
        return null;
    }
  };

  const currentQuestion = getCurrentQuestion();

  if (!currentQuestion) {
    return <div>Ошибка</div>;
  }

  if (step === 4) {
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
        <h1>Тест завершен!</h1>
        <p>Спасибо за участие!</p>
        <button onClick={() => console.log(answers)}>Посмотреть ответы</button>
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
      <h1>Ответь на пару вопросов</h1>
      <p>{currentQuestion.text}</p>
      <div>
        <button 
          onClick={() => saveAnswer(currentQuestion.key, 'да')}
        >да</button>
        <button 
          onClick={() => saveAnswer(currentQuestion.key, 'нет')}
        >нет</button>
      </div>
    </div>
  );
}

export default Questions;