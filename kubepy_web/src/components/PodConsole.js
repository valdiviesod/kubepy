import React, { useState } from 'react';
import axios from 'axios';

const PodConsole = () => {
    const [command, setCommand] = useState('');
    const [output, setOutput] = useState('');
    const [history, setHistory] = useState([]);

    const handleCommandChange = (e) => {
        setCommand(e.target.value);
    };

    const handleCommandSubmit = async (e) => {
        e.preventDefault();

        if (command.trim() === '') return;

        try {
            const response = await axios.post('http://207.248.81.113:5000/pods/test1/exec', {
                command
            });

            // Update output and history
            setHistory([...history, `> ${command}`, response.data.output]);
            setOutput(response.data.output);
        } catch (error) {
            setHistory([...history, `> ${command}`, `Error: ${error.response ? error.response.data.msg : 'Server Error'}`]);
        }

        // Clear the command input
        setCommand('');
    };

    return (
        <div style={styles.consoleContainer}>
            <div style={styles.consoleOutput}>
                {history.map((line, index) => (
                    <div key={index} style={styles.consoleLine}>{line}</div>
                ))}
            </div>
            <form onSubmit={handleCommandSubmit} style={styles.consoleForm}>
                <span style={styles.promptSymbol}>$</span>
                <input
                    type="text"
                    value={command}
                    onChange={handleCommandChange}
                    style={styles.consoleInput}
                    placeholder="Enter command"
                    autoFocus
                />
            </form>
        </div>
    );
};

const styles = {
    consoleContainer: {
        backgroundColor: '#000',
        color: '#fff',
        fontFamily: 'monospace',
        padding: '10px',
        borderRadius: '5px',
        width: '100%',
        maxWidth: '600px',
        margin: '0 auto',
    },
    consoleOutput: {
        height: '300px',
        overflowY: 'auto',
        marginBottom: '10px',
        padding: '10px',
        backgroundColor: '#111',
        borderRadius: '5px',
    },
    consoleForm: {
        display: 'flex',
        alignItems: 'center',
    },
    promptSymbol: {
        marginRight: '10px',
    },
    consoleInput: {
        flexGrow: 1,
        backgroundColor: '#000',
        color: '#fff',
        border: 'none',
        outline: 'none',
        fontFamily: 'monospace',
        fontSize: '16px',
    },
    consoleLine: {
        marginBottom: '5px',
    },
};

export default PodConsole;
