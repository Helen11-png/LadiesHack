import { BrowserRouter, Routes, Route, Link } from 'react-router-dom';
import Home from './pages/home';
import Questions from './pages/questions';
import Page1 from './pages/1';
import Page2 from './pages/2';

function App() {
  return (
    <BrowserRouter>
      <nav style={{ padding: '20px', background: '#333', color: 'white' }}>
        <Link to="/" style={{ marginRight: '15px', color: 'white' }}>Главная</Link>
      </nav>
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/questions" element={<Questions />} />
        <Route path="/1" element={<Page1 />} />
        <Route path="/2" element={<Page2 />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;