// Competitive Coding Platform Server
// Node.js + Express server for hosting the platform and handling code execution

const express = require('express');
const path = require('path');
const { exec } = require('child_process');
const fs = require('fs').promises;
const bodyParser = require('body-parser');

const app = express();
const PORT = 8000;

// Middleware
app.use(bodyParser.json());
app.use(express.static('public')); // Serve static files (HTML, CSS, JS)

// Serve the main editor page
app.get('/', (req, res) => {
    res.sendFile(path.join(__dirname, 'public', 'editor.html'));
});

// API endpoint to submit and execute code
app.post('/api/submit-code', async (req, res) => {
    const { code, language, problemId } = req.body;
    
    try {
        // Create a temporary file for the code
        const timestamp = Date.now();
        const filename = `submission_${timestamp}`;
        
        let result;
        
        if (language === 'cpp') {
            // Handle C++ code
            // 1. Save the C++ code to a temporary file
            const cppFile = path.join(__dirname, 'temp', `${filename}.cpp`);
            await fs.mkdir(path.join(__dirname, 'temp'), { recursive: true });
            await fs.writeFile(cppFile, code);
            
            // 2. Call your C++ to Python transpiler
            // This is where you'd integrate your transpiler
            const pythonFile = path.join(__dirname, 'temp', `${filename}.py`);
            
            // Example transpiler call (adjust to your actual transpiler)
            await runTranspiler(cppFile, pythonFile);
            
            // 3. Execute the generated Python code
            result = await executePython(pythonFile);
            
            // Cleanup
            await cleanup([cppFile, pythonFile]);
            
        } else if (language === 'python') {
            // Handle direct Python submissions
            const pythonFile = path.join(__dirname, 'temp', `${filename}.py`);
            await fs.mkdir(path.join(__dirname, 'temp'), { recursive: true });
            await fs.writeFile(pythonFile, code);
            
            result = await executePython(pythonFile);
            
            // Cleanup
            await cleanup([pythonFile]);
        }
        
        res.json({
            success: true,
            output: result.output,
            error: result.error,
            executionTime: result.executionTime
        });
        
    } catch (error) {
        res.status(500).json({
            success: false,
            error: error.message
        });
    }
});

// Function to run the C++ to Python transpiler
async function runTranspiler(cppFilePath, pythonFilePath) {
    return new Promise((resolve, reject) => {
        // Replace this with your actual transpiler command
        // Example: exec(`./transpiler ${cppFilePath} ${pythonFilePath}`, ...)
        const transpilerCommand = `python3 transpiler.py ${cppFilePath} -o ${pythonFilePath}`;
        
        exec(transpilerCommand, (error, stdout, stderr) => {
            if (error) {
                reject(new Error(`Transpiler error: ${stderr || error.message}`));
                return;
            }
            resolve(stdout);
        });
    });
}

// Function to execute Python code
async function executePython(pythonFilePath) {
    return new Promise((resolve, reject) => {
        const startTime = Date.now();
        
        // Set a timeout to prevent infinite loops (5 seconds)
        const timeout = 5000;
        
        const process = exec(
            `python3 ${pythonFilePath}`,
            { timeout: timeout },
            (error, stdout, stderr) => {
                const executionTime = Date.now() - startTime;
                
                if (error) {
                    // Check if it's a timeout error
                    if (error.killed) {
                        resolve({
                            output: '',
                            error: 'Execution timed out (5 seconds limit)',
                            executionTime: timeout
                        });
                    } else {
                        resolve({
                            output: stdout,
                            error: stderr || error.message,
                            executionTime: executionTime
                        });
                    }
                    return;
                }
                
                resolve({
                    output: stdout,
                    error: stderr,
                    executionTime: executionTime
                });
            }
        );
    });
}

// Function to clean up temporary files
async function cleanup(files) {
    for (const file of files) {
        try {
            await fs.unlink(file);
        } catch (error) {
            console.error(`Failed to delete ${file}:`, error.message);
        }
    }
}

// API endpoint to get problem details
app.get('/api/problem/:id', (req, res) => {
    const problemId = req.params.id;
    
    // This would typically fetch from a database
    // For now, returning mock data
    const problems = {
        '1': {
            id: 1,
            title: 'Two Sum',
            description: 'Given an array of integers nums and an integer target, return indices of the two numbers such that they add up to target.',
            examples: [
                {
                    input: 'nums = [2,7,11,15], target = 9',
                    output: '[0,1]',
                    explanation: 'Because nums[0] + nums[1] == 9, we return [0, 1].'
                }
            ],
            difficulty: 'Easy'
        }
    };
    
    const problem = problems[problemId];
    if (problem) {
        res.json(problem);
    } else {
        res.status(404).json({ error: 'Problem not found' });
    }
});

// Start the server
app.listen(PORT, () => {
    console.log(`🚀 Server is running on http://localhost:${PORT}/`);
    console.log(`📝 Editor available at http://localhost:${PORT}/`);
    console.log(`🔧 API endpoints:`);
    console.log(`   POST /api/submit-code - Submit code for execution`);
    console.log(`   GET  /api/problem/:id - Get problem details`);
});
