import subprocess
import os
import sys
import time
import signal

def main():
    print("🚀 Starting Pokemon Battle Sim Development Servers...")
    
    # Define paths
    root_dir = os.path.dirname(os.path.abspath(__file__))
    backend_dir = os.path.join(root_dir, "backend")
    frontend_dir = os.path.join(root_dir, "frontend")
    
    processes = []
    
    try:
        # 1. Start Backend
        print("📡 Starting Backend (FastAPI) on port 7860...")
        backend_process = subprocess.Popen(
            [sys.executable, "-m", "src.core.fastapi_server"],
            cwd=backend_dir
        )
        processes.append(backend_process)
        
        # 2. Start Frontend
        print("💻 Starting Frontend (Next.js) on port 3000...")
        # Check if npm is available
        npm_cmd = "npm.cmd" if os.name == "nt" else "npm"
        frontend_process = subprocess.Popen(
            [npm_cmd, "run", "dev"],
            cwd=frontend_dir
        )
        processes.append(frontend_process)
        
        print("\n✅ Both servers are launching!")
        print("🔗 Frontend: http://localhost:3000")
        print("🔗 Backend: http://localhost:7860")
        print("-" * 40)
        print("Press Ctrl+C to stop both servers.")
        
        # Keep the script running
        while True:
            time.sleep(1)
            # Check if processes are still running
            if backend_process.poll() is not None:
                print("❌ Backend process stopped unexpectedly.")
                break
            if frontend_process.poll() is not None:
                print("❌ Frontend process stopped unexpectedly.")
                break
                
    except KeyboardInterrupt:
        print("\nStopping servers...")
    finally:
        # Terminate all processes
        for p in processes:
            try:
                if os.name == "nt":
                    p.terminate()
                else:
                    os.kill(p.pid, signal.SIGTERM)
            except:
                pass
        print("👋 Servers stopped.")

if __name__ == "__main__":
    main()
