import React, { useState, useEffect } from 'react';
import backgroundImage from '../images/2.jpg';
import './questions.css';

function Page2() {
  const [inventory, setInventory] = useState<string[]>([]);
  const [selectedInsurances, setSelectedInsurances] = useState<string[]>([]);
  const [showResults, setShowResults] = useState(false);

  // Список доступных страховок
  const insuranceOptions = [
    { id: 'card', name: '🏦 Страхование банковской карты', emoji: '💳' },
    { id: 'home', name: '🏠 Страхование жилья', emoji: '🔑' },
    { id: 'travel', name: '✈️ Страхование билетов для путешествий', emoji: '🎫' },
    { id: 'tech', name: '📱 Страхование на электронную технику', emoji: '💻' }
  ];

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

  const handleSelectInsurance = (insuranceName: string) => {
    if (selectedInsurances.includes(insuranceName)) {
      // Если уже выбрана, убираем
      const newSelected = selectedInsurances.filter(item => item !== insuranceName);
      setSelectedInsurances(newSelected);
    } else {
      // Если еще не выбрана и выбрано меньше 3, добавляем
      if (selectedInsurances.length < 3) {
        const newSelected = [...selectedInsurances, insuranceName];
        setSelectedInsurances(newSelected);
      } else {
        alert('Ты можешь выбрать только 3 страховки!');
      }
    }
  };

  const handleConfirm = () => {
    if (selectedInsurances.length === 0) {
      alert('Выбери хотя бы одну страховку!');
      return;
    }
    
    const newInventory = [...inventory, ...selectedInsurances];
    saveInventory(newInventory);
    alert(`Добавлено в инвентарь: ${selectedInsurances.join(', ')}`);
    setSelectedInsurances([]);
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
        background: 'rgba(255, 255, 255, 0.95)',
        borderRadius: '20px',
        padding: '30px',
        maxWidth: '600px',
        width: '100%',
        boxShadow: '0 10px 30px rgba(0,0,0,0.2)'
      }}>
        <h1>🎒 Твой инвентарь:</h1>
        
        <div style={{
          background: '#f0f0f0',
          borderRadius: '15px',
          padding: '20px',
          margin: '20px 0',
          textAlign: 'left',
          minHeight: '100px'
        }}>
          {inventory.length === 0 ? (
            <p style={{ color: '#999', textAlign: 'center' }}>Здесь пока пусто</p>
          ) : (
            inventory.map((item, index) => (
              <div key={index} style={{ padding: '5px 0', fontSize: '16px' }}>✅ {item}</div>
            ))
          )}
        </div>

        <p style={{ fontSize: '18px', margin: '20px 0', fontWeight: 'bold' }}>
          📋 Страховки уходят в инвентарь
        </p>

        <p style={{ fontSize: '16px', margin: '10px 0' }}>
          Выбери страховки (до 3):
          <span style={{ color: '#ff6b6b', marginLeft: '10px' }}>
            {selectedInsurances.length}/3 выбрано
          </span>
        </p>

        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))',
          gap: '12px',
          margin: '20px 0'
        }}>
          {insuranceOptions.map((insurance) => (
            <button
              key={insurance.id}
              onClick={() => handleSelectInsurance(insurance.name)}
              style={{
                background: selectedInsurances.includes(insurance.name) 
                  ? '#4ecdc4' 
                  : 'rgba(200, 200, 200, 0.5)',
                color: selectedInsurances.includes(insurance.name) ? 'white' : 'black',
                padding: '12px 16px',
                fontSize: '14px',
                border: selectedInsurances.includes(insurance.name) 
                  ? '2px solid #4ecdc4' 
                  : '2px solid #ddd',
                borderRadius: '10px',
                cursor: 'pointer',
                transition: '0.3s',
                textAlign: 'left'
              }}
            >
              {insurance.emoji} {insurance.name}
              {selectedInsurances.includes(insurance.name) && ' ✓'}
            </button>
          ))}
        </div>

        <button
          onClick={handleConfirm}
          style={{
            background: '#ff6b6b',
            color: 'white',
            padding: '14px 28px',
            fontSize: '18px',
            border: 'none',
            borderRadius: '12px',
            cursor: 'pointer',
            marginTop: '10px',
            width: '100%',
            fontWeight: 'bold'
          }}
          onMouseEnter={(e) => e.currentTarget.style.transform = 'scale(1.02)'}
          onMouseLeave={(e) => e.currentTarget.style.transform = 'scale(1)'}
        >
          ✅ Добавить выбранные страховки в инвентарь
        </button>

        <button
          onClick={() => setShowResults(!showResults)}
          style={{
            marginTop: '20px',
            background: '#95a5a6',
            color: 'white',
            padding: '10px 20px',
            border: 'none',
            borderRadius: '8px',
            cursor: 'pointer',
            width: '100%'
          }}
        >
          {showResults ? 'Скрыть' : 'Показать'} весь инвентарь
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
            <pre style={{ fontSize: '12px', overflow: 'auto' }}>{JSON.stringify(inventory, null, 2)}</pre>
          </div>
        )}
      </div>
    </div>
  );
}

export default Page2;