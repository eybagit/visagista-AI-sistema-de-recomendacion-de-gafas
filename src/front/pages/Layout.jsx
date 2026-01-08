import { Outlet } from "react-router-dom/dist"
import ScrollToTop from "../components/ScrollToTop"

// Layout limpio para el sistema de Visagista Óptico IA
// Removidos Navbar y Footer del boilerplate original
export const Layout = () => {
    return (
        <ScrollToTop>
            <Outlet />
        </ScrollToTop>
    )
}