import React from "react";
import Chatbot from "./Chatbot";

interface SideMenuProps {
    isOpen: boolean;
    toggleMenu: () => void;
}

const ChatMenu: React.FC<SideMenuProps> = ({ isOpen }) => {
    return <>{isOpen && <Chatbot />}</>;
};

export default ChatMenu;
