import { BrowserRouter, Routes, Route, Link } from 'react-router-dom';
import Home from './pages/home';
import Questions from './pages/questions';

function App() {
  return (
    <BrowserRouter>
      <nav style={{ padding: '20px', background: '#333', color: 'white' }}>
        <Link to="/" style={{ marginRight: '15px', color: 'white' }}>Главная</Link>
      </nav>
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/questions" element={<Questions />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;