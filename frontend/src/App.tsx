import { Route, Routes } from 'react-router-dom'
import NavBar from './components/NavBar'
import Footer from './components/Footer'
import ChatWidget from './components/ChatWidget'
import SnapButton from './components/SnapButton'
import Home from './pages/Home'
import Products from './pages/Products'
import ProductDetail from './pages/ProductDetail'
import About from './pages/About'
import LogIn from './pages/LogIn'
import CreateAccount from './pages/CreateAccount'
import VerifyEmail from './pages/VerifyEmail'
import NotFound from './pages/NotFound'

export default function App() {
  return (
    <>
      <NavBar />
      <main className="site-main">
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/products" element={<Products />} />
          <Route path="/products/:productId" element={<ProductDetail />} />
          <Route path="/about" element={<About />} />
          <Route path="/login" element={<LogIn />} />
          <Route path="/create-account" element={<CreateAccount />} />
          <Route path="/verify-email" element={<VerifyEmail />} />
          <Route path="*" element={<NotFound />} />
        </Routes>
      </main>
      <Footer />
      <ChatWidget />
      {import.meta.env.DEV && <SnapButton />}
    </>
  )
}
