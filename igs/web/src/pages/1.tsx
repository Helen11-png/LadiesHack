import React, { useState, useEffect } from 'react';
import backgroundImage from '../images/2.jpg';
import './questions.css';

function Page1() {
  const [inventory, setInventory] = useState<string[]>([]);
  const [showResults, setShowResults] = useState(false);

  // Загрузка инвентаря из сохраненных данных
  useEffect(() => {
    const savedInventory = localStorage.getItem('inventory');
    if (savedInventory) {
      setInventory(JSON.parse(savedInventory));
    }
  }, []);

  const saveInventory = (newInventory: string[]) => {
    setInventory(newInventory);
    localStorage.setItem('inventory', JSON.stringify(newInventory));
  };

  const handleChoice = (choice: string) => {
    if (choice === 'Выбрать страховку') {
      const newInventory = [...inventory, '📄 Страховка'];
      saveInventory(newInventory);
      alert('Страховка добавлена в инвентарь!');
    } else if (choice === 'Не хочу страховку') {
      alert('Ты отказался от страховки. Будь осторожен!');
    }
  };

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
      <div style={{
        background: 'rgba(255, 255, 255, 0.9)',
        borderRadius: '20px',
        padding: '30px',
        maxWidth: '500px',
        width: '100%',
        boxShadow: '0 10px 30px rgba(0,0,0,0.2)'
      }}>
        <h1>🤔 Кто ты: везунчик или катастрофа?</h1>
        
        <div style={{
          background: '#f0f0f0',
          borderRadius: '15px',
          padding: '20px',
          margin: '20px 0',
          textAlign: 'left'
        }}>
          <h3>🎒 Твой инвентарь:</h3>
          {inventory.length === 0 ? (
            <p style={{ color: '#999' }}>Здесь пока пусто</p>
          ) : (
            <ul style={{ listStyle: 'none', padding: 0 }}>
              {inventory.map((item, index) => (
                <li key={index} style={{ padding: '5px 0', fontSize: '18px' }}>{item}</li>
              ))}
            </ul>
          )}
        </div>

        <p style={{ fontSize: '18px', margin: '20px 0' }}>
          💰 Родители дали тебе карманные деньги:
        </p>

        <div style={{ display: 'flex', gap: '15px', justifyContent: 'center', flexWrap: 'wrap' }}>
          <button
            onClick={() => handleChoice('Не хочу страховку')}
            style={{
              background: '#ff6b6b',
              color: 'white',
              padding: '12px 24px',
              fontSize: '16px',
              border: 'none',
              borderRadius: '10px',
              cursor: 'pointer',
              transition: '0.3s'
            }}
            onMouseEnter={(e) => e.currentTarget.style.transform = 'scale(1.05)'}
            onMouseLeave={(e) => e.currentTarget.style.transform = 'scale(1)'}
          >
            ❌ Не хочу страховку
          </button>
          
          <button
            onClick={() => handleChoice('Выбрать страховку')}
            style={{
              background: '#4ecdc4',
              color: 'white',
              padding: '12px 24px',
              fontSize: '16px',
              border: 'none',
              borderRadius: '10px',
              cursor: 'pointer',
              transition: '0.3s'
            }}
            onMouseEnter={(e) => e.currentTarget.style.transform = 'scale(1.05)'}
            onMouseLeave={(e) => e.currentTarget.style.transform = 'scale(1)'}
          >
            ✅ Выбрать страховку
          </button>
        </div>

        <button
          onClick={() => setShowResults(!showResults)}
          style={{
            marginTop: '30px',
            background: '#95a5a6',
            color: 'white',
            padding: '10px 20px',
            border: 'none',
            borderRadius: '8px',
            cursor: 'pointer'
          }}
        >
          {showResults ? 'Скрыть' : 'Показать'} инвентарь
        </button>

        {showResults && (
          <div style={{
            background: '#e8e8e8',
            padding: '15px',
            borderRadius: '10px',
            marginTop: '20px',
            textAlign: 'left'
          }}>
            <h4>📦 Сохраненный инвентарь:</h4>
            <pre style={{ fontSize: '12px' }}>{JSON.stringify(inventory, null, 2)}</pre>
          </div>
        )}
      </div>
    </div>
  );
}

export default Page1;