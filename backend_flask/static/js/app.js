mermaid.initialize({ startOnLoad: false, theme: 'dark' });

    // State
    let isLoginMode = true;
    let currentRecordId = null;
    let currentFlashcards = [];
    let sessionUploadCount = 0;

    // DOM Elements
    const authScreen = document.getElementById('authScreen'), mainApp = document.getElementById('mainApp');
    const authForm = document.getElementById('authForm'), authToggleBtn = document.getElementById('authToggleBtn');
    const authSubmitBtn = document.getElementById('authSubmitBtn'), authError = document.getElementById('authError');
    const welcomeText = document.getElementById('welcomeText'), logoutBtn = document.getElementById('logoutBtn');
    const deckList = document.getElementById('deckList');
    
    // Auth Logic
    async function fetchUserStatus() {
        try {
            const token = localStorage.getItem('token');
            const res = await fetch('/api/status', {
                headers: { 'Authorization': 'Bearer ' + token }
            });
            if (res.ok) {
                const data = await res.json();
                document.getElementById('usageStats').style.display = 'inline-block';
                document.getElementById('usageCount').textContent = data.generations_used;
            }
        } catch (e) {
            console.error('Failed to fetch user status:', e);
        }
    }

    function checkAuth() {
      const token = localStorage.getItem('token');
      const username = localStorage.getItem('username');
      if (token && username) {
        authScreen.style.display = 'none';
        mainApp.style.display = 'flex';
        welcomeText.textContent = `Welcome, ${username}`;
        loadDecks();
        fetchUserStatus();
      } else {
        authScreen.style.display = 'flex';
        mainApp.style.display = 'none';
      }
    }
    checkAuth();

    authToggleBtn.onclick = () => {
      isLoginMode = !isLoginMode;
      authSubmitBtn.textContent = isLoginMode ? 'Login' : 'Register';
      authToggleBtn.textContent = isLoginMode ? "Don't have an account? Register here" : "Already have an account? Login here";
      authError.style.display = 'none';
    };

    authForm.onsubmit = async (e) => {
      e.preventDefault();
      const endpoint = isLoginMode ? '/api/login' : '/api/register';
      const user = document.getElementById('username').value;
      const pass = document.getElementById('password').value;
      
      try {
        const res = await fetch(endpoint, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ username: user, password: pass })
        });
        const data = await res.json();
        if (res.ok) {
          if (isLoginMode) {
            localStorage.setItem('token', data.access_token);
            localStorage.setItem('username', data.username);
            checkAuth();
          } else {
            alert('Registration successful. Please login.');
            authToggleBtn.click();
          }
        } else {
          authError.textContent = data.error || 'Authentication failed';
          authError.style.display = 'block';
        }
      } catch (err) {
        authError.textContent = 'Network error';
        authError.style.display = 'block';
      }
    };

    logoutBtn.onclick = () => {
      localStorage.removeItem('token');
      localStorage.removeItem('username');
      checkAuth();
    };

    // Helper: Auth Fetch (with 60s timeout)
    async function fetchWithAuth(url, options = {}) {
      const token = localStorage.getItem('token');
      if (!options.headers) options.headers = {};
      options.headers['Authorization'] = `Bearer ${token}`;
      
      // Add a 60 second timeout to prevent indefinite hangs
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 60000);
      options.signal = controller.signal;
      
      try {
        const res = await fetch(url, options);
        clearTimeout(timeoutId);
        if (res.status === 401) {
          alert("Session expired. Please login again.");
          logoutBtn.click();
          throw new Error("Unauthorized");
        }
        return res;
      } catch (e) {
        clearTimeout(timeoutId);
        throw e;
      }
    }

    // Helper: Fetch with Retry
    async function fetchWithRetry(url, options = {}, maxRetries = 10, delayMs = 5000) {
      let lastError;
      for (let i = 0; i < maxRetries; i++) {
        try {
          // Check network status before fetching
          if (!navigator.onLine) {
             throw new Error("You are offline.");
          }
          const res = await fetchWithAuth(url, options);
          // If we get a 500 or 502/503/504, we might want to retry.
          // But if it's 401 or 400 (validation), we probably shouldn't retry, but let's keep it simple.
          if (!res.ok && res.status >= 500) {
              const errText = await res.text();
              throw new Error(`Server Error: ${res.status} ${errText}`);
          }
          return res;
        } catch (e) {
          lastError = e;
          console.warn(`Fetch attempt ${i + 1} failed:`, e);
          if (i < maxRetries - 1) {
             // Update UI to let user know we are retrying if possible
             const pText = document.getElementById('generationMessage');
             if (pText && document.getElementById('generationOverlay').style.display !== 'none') {
                 // append (Retrying x/10) to current text if not already there
                 let currentMsg = pText.textContent;
                 if (currentMsg.includes('(Retrying')) {
                     currentMsg = currentMsg.replace(/\(Retrying.*\)/, `(Retrying ${i + 1}/${maxRetries})`);
                 } else {
                     currentMsg = `${currentMsg} (Retrying ${i + 1}/${maxRetries})`;
                 }
                 pText.textContent = currentMsg;
             }
             await new Promise(resolve => setTimeout(resolve, delayMs));
          }
        }
      }
      throw new Error(`The system is currently offline or overloaded. Please try using it later. (Failed after ${maxRetries} attempts)`);
    }

    // Load Decks (Documents)
    async function loadDecks(autoSelectLatest = false) {
      try {
        const res = await fetchWithAuth('/api/list-generated');
        const data = await res.json();
        deckList.innerHTML = '';
        if (data.length === 0) {
          deckList.innerHTML = '<p class="empty-state" style="padding:0">No documents yet.</p>';
          return;
        }
        let latestDiv = null;
        let latestRecord = null;
        data.forEach((record, idx) => {
          const div = document.createElement('div');
          div.className = 'deck-item';
          div.style.position = 'relative'; // For absolute positioning of trash icon
          
          div.innerHTML = `
            <div class="deck-title" style="padding-right: 20px;">${record.source_file}</div>
            <div class="deck-meta">${record.flashcards ? record.flashcards.length : 0} cards • ${new Date(record.created_at).toLocaleDateString()}</div>
            <button class="delete-doc-btn" onclick="deleteDocument(event, '${record._id}')" title="Delete Document">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <polyline points="3 6 5 6 21 6"></polyline>
                    <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>
                </svg>
            </button>
          `;
          div.onclick = () => selectDeck(record, div);
          deckList.appendChild(div);
          if (idx === 0) {
             latestDiv = div;
             latestRecord = record;
          }
        });
        
        if (autoSelectLatest && latestDiv) {
           latestDiv.click();
        }
      } catch(e) { console.error(e); }
    }

    async function deleteDocument(event, recordId) {
        event.stopPropagation(); // Prevent selectDeck from firing
        if (!confirm("Are you sure you want to delete this document? This cannot be undone.")) return;
        
        try {
            const res = await fetchWithAuth('/api/documents/' + recordId, { method: 'DELETE' });
            if (res.ok) {
                if (currentRecordId === recordId) {
                    // Reset view if the deleted document was currently open
                 if (!currentFlashcards || currentFlashcards.length === 0) {
                    document.getElementById('flashcardsEmpty').style.display = 'block';
                }    document.getElementById('topicsContent').style.display = 'none';
                    document.getElementById('quizEmpty').style.display = 'block';
                    document.getElementById('quizContent').style.display = 'none';
                    document.getElementById('mindmapEmpty').style.display = 'block';
                    document.getElementById('mindmapContent').style.display = 'none';
                    document.getElementById('openBatchModalBtn').style.display = 'none';
                    document.getElementById('flashcardsContainer').innerHTML = '';
                }
                loadDecks();
            } else {
                alert("Failed to delete document.");
            }
        } catch (e) {
            console.error(e);
            alert("Network error while deleting document.");
        }
    }

    function selectDeck(record, element) {
      document.querySelectorAll('.deck-item').forEach(el => el.classList.remove('active'));
      element.classList.add('active');
      currentRecordId = record._id;
      currentFlashcards = record.flashcards;
      
      // Update UI state
      document.getElementById('flashcardsEmpty').style.display = 'none';
      document.getElementById('topicsEmpty').style.display = 'none';
      document.getElementById('topicsContent').style.display = 'block';
      document.getElementById('quizEmpty').style.display = 'none';
      document.getElementById('quizContent').style.display = 'block';
      document.getElementById('mindmapEmpty').style.display = 'none';
      document.getElementById('mindmapContent').style.display = 'block';
      

      // Clear previous AI results
      document.getElementById('topicsResult').innerHTML = '';
      document.getElementById('quizResult').innerHTML = '';
      document.getElementById('mindmapResult').innerHTML = '';
      
      // Hide buttons by default
      document.getElementById('generateFlashcardsBtn').style.display = 'none';
      document.getElementById('generateTopicsBtn').style.display = 'none';
      document.getElementById('generateQuizBtn').style.display = 'none';
      document.getElementById('generateMindmapBtn').style.display = 'none';
      
      let hasAnyContent = false;
      if (record.topics) { renderTopics(record.topics); hasAnyContent = true; } else { document.getElementById('generateTopicsBtn').style.display = 'block'; }
      if (record.quiz && record.quiz.length > 0) { renderQuiz(record.quiz); hasAnyContent = true; } else { document.getElementById('generateQuizBtn').style.display = 'block'; }
      if (record.mindmap) { renderMindmap(record.mindmap); hasAnyContent = true; } else { document.getElementById('generateMindmapBtn').style.display = 'block'; }
      if (record.flashcards && record.flashcards.length > 0) { hasAnyContent = true; }

      renderFlashcards();
      
      if (window.innerWidth <= 768) {
          document.querySelector('.sidebar').classList.remove('active');
      }
    }

    // Render Flashcards with Voice
    function renderFlashcards() {
      const container = document.getElementById('flashcardsContainer');
      container.innerHTML = '';
      
      if (!currentFlashcards || currentFlashcards.length === 0) {
        document.getElementById('generateFlashcardsBtn').style.display = 'block';
        document.getElementById('generateFlashcardsBtn').textContent = 'Generate Flashcards';
        return;
      }
      document.getElementById('generateFlashcardsBtn').style.display = 'block';
      document.getElementById('generateFlashcardsBtn').textContent = 'Regenerate Flashcards';
      
      currentFlashcards.forEach((card, index) => {
        const wrapper = document.createElement('div');
        wrapper.className = 'flashcard-wrapper';
        wrapper.innerHTML = `
          <div class="flashcard" onclick="this.classList.toggle('is-flipped')">
            <div class="flashcard-face">
              <button class="play-btn" onclick="event.stopPropagation(); playVoice(this, ${index})">▶</button>
              <h3 style="margin-bottom:0.5rem; color:var(--primary);">Q:</h3>
              <p>${card.question}</p>
            </div>
            <div class="flashcard-face flashcard-back">
              <h3 style="margin-bottom:0.5rem; color:var(--success);">A:</h3>
              <p>${card.answer}</p>
            </div>
          </div>
        `;
        container.appendChild(wrapper);
      });
    }

    function playVoice(btn, index) {
      const cardData = currentFlashcards[index];
      const cardElement = btn.closest('.flashcard');
      
      window.speechSynthesis.cancel();
      
      const uFront = new SpeechSynthesisUtterance(cardData.question);
      const uBack = new SpeechSynthesisUtterance(cardData.answer);
      
      // Ensure card is showing front
      cardElement.classList.remove('is-flipped');
      
      uFront.onend = () => {
        // Flip card after reading front
        cardElement.classList.add('is-flipped');
        setTimeout(() => {
          window.speechSynthesis.speak(uBack);
        }, 500); // Wait for flip animation
      };
      
      window.speechSynthesis.speak(uFront);
    }

    // Tabs Logic
    document.querySelectorAll('.tab-btn').forEach(btn => {
      btn.onclick = () => {
        document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
        document.querySelectorAll('.tab-pane').forEach(p => p.classList.remove('active'));
        btn.classList.add('active');
        document.getElementById(`tab-${btn.dataset.tab}`).classList.add('active');
      };
    });

    function checkAnswer(qIdx, optIdx, correctIdx) {
      const qDiv = document.getElementById(`q-${qIdx}`);
      const options = qDiv.querySelectorAll('.quiz-option');
      options.forEach(opt => {
        opt.style.pointerEvents = 'none';
        opt.classList.remove('correct', 'wrong');
      });
      if (optIdx === correctIdx) {
        options[optIdx].classList.add('correct');
      } else {
        options[optIdx].classList.add('wrong');
        options[correctIdx].classList.add('correct');
      }
      document.getElementById(`exp-${qIdx}`).style.display = 'block';
    }

    // Upload Logic
    const uploadBox = document.getElementById('uploadBox');
    const fileInput = document.getElementById('fileInput');
    uploadBox.onclick = () => fileInput.click();
    
    fileInput.onchange = async (e) => {
        const file = e.target.files[0];
        if (!file) return;
        
        const formData = new FormData();
        formData.append('file', file);
        
        document.getElementById('uploadBox').style.pointerEvents = 'none';
        document.getElementById('uploadBox').style.opacity = '0.5';
        document.getElementById('uploadSpinner').style.display = 'inline-block';
        
        try {
            const res = await fetchWithAuth('/api/upload', {
                method: 'POST',
                body: formData
            }, false); // don't set Content-Type header for FormData
            
            if (res.ok) {
                await loadDecks(true); // Automatically select the newly uploaded deck
                if (window.innerWidth <= 768) {
                    document.querySelector('.sidebar').classList.remove('active');
                }
            } else {
                const data = await res.json();
                alert('Upload failed: ' + data.error);
            }
        } catch(e) {
            alert('Upload failed. Please try again.');
        } finally {
            document.getElementById('uploadBox').style.pointerEvents = 'auto';
            document.getElementById('uploadBox').style.opacity = '1';
            document.getElementById('uploadSpinner').style.display = 'none';
            document.getElementById('fileInput').value = '';
        }
    };

    // Mobile menu toggle
    const mobileMenuBtn = document.getElementById('mobileMenuBtn');
    if (mobileMenuBtn) {
        mobileMenuBtn.onclick = () => {
            document.querySelector('.sidebar').classList.toggle('active');
        };
    }

    // AI API Callers

    // Core AI Call function (still used by individual buttons if they were visible)
    async function callAI(endpoint, actionType, onSuccess) {
      if (!currentRecordId) return alert('Select a document first');
      
      startGenerationOverlay(`Generating ${actionType}...`);
      
      let progress = 5;
      setGenerationProgress(progress, `Generating ${actionType}...`);
      
      // Fake progress interval
      const progressInterval = setInterval(() => {
          if (progress < 90) {
              // Slower progress as it gets higher
              const increment = progress < 50 ? 5 : (progress < 80 ? 2 : 1);
              progress += increment;
              setGenerationProgress(progress, `Generating ${actionType}...`);
          }
      }, 1000);
      
      try {
        const res = await fetchWithRetry(endpoint, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ record_id: currentRecordId })
        });
        const data = await res.json();
        if (!res.ok) throw new Error(data.error || 'Failed to generate');
        
        clearInterval(progressInterval);
        setGenerationProgress(100, `Done!`);
        await onSuccess(data.data);
        
        fetchUserStatus(); // Update AI generation count
      } catch (e) {
        clearInterval(progressInterval);
        alert(e.message);
      } finally {
        stopGenerationOverlay();
      }
    }

    // Render Functions
    function renderTopics(markdown) {
      document.getElementById('topicsResult').innerHTML = marked.parse(markdown);
      document.getElementById('generateTopicsBtn').style.display = 'none';
    }

    function renderQuiz(quizData) {
      let html = '';
      quizData.forEach((q, i) => {
        html += `
          <div class="quiz-question" id="q-${i}">
            <h3>${i + 1}. ${q.question}</h3>
            ${q.options.map((opt, optIdx) => `<div class="quiz-option" onclick="checkAnswer(${i}, ${optIdx}, ${q.correct_index})">${opt}</div>`).join('')}
            <div class="quiz-explanation" id="exp-${i}">${q.explanation}</div>
          </div>`;
      });
      document.getElementById('quizResult').innerHTML = html;
      document.getElementById('generateQuizBtn').style.display = 'none';
    }

    async function renderMindmap(mermaidText) {
      const container = document.getElementById('mindmapResult');
      try {
        let cleanText = mermaidText;
        if (cleanText.includes("```mermaid")) {
            cleanText = cleanText.split("```mermaid")[1].split("```")[0].trim();
        } else if (cleanText.includes("```")) {
            cleanText = cleanText.replace(/```/g, "").trim();
        }
        
        container.innerHTML = `<div class="mermaid">${cleanText}</div>`;
        
        // Force display block temporarily if hidden, as mermaid fails on display:none
        const mindmapPane = document.getElementById('tab-mindmap');
        const wasHidden = mindmapPane && !mindmapPane.classList.contains('active');
        if (wasHidden) {
            mindmapPane.style.display = 'block';
            mindmapPane.style.position = 'absolute';
            mindmapPane.style.visibility = 'hidden';
        }
        
        try {
            await Promise.race([
                mermaid.run({ nodes: container.querySelectorAll('.mermaid') }),
                new Promise((_, reject) => setTimeout(() => reject(new Error("Mermaid render timeout")), 5000))
            ]);
        } finally {
            if (wasHidden) {
                mindmapPane.style.display = '';
                mindmapPane.style.position = '';
                mindmapPane.style.visibility = '';
            }
        }
        
        // Enable Pan/Zoom after rendering
        const svgElement = container.querySelector('svg');
        if (svgElement && window.svgPanZoom) {
            svgElement.style.width = "100%";
            svgElement.style.height = "500px";
            svgPanZoom(svgElement, { controlIconsEnabled: true, zoomEnabled: true, panEnabled: true });
        }
        document.getElementById('generateMindmapBtn').style.display = 'none';
      } catch (e) {
        console.error("Mermaid parsing error:", e);
        container.innerHTML = `<p style="color:var(--danger)">Failed to render mind map. Syntax error in generated code.</p><pre>${mermaidText}</pre>`;
      }
    }

    // Flashcards
    document.getElementById('generateFlashcardsBtn').onclick = () => {
      callAI('/api/generate-flashcards', 'flashcards', (flashcards) => {
        currentFlashcards = flashcards;
        renderFlashcards();
      });
    };

    // Topics
    document.getElementById('generateTopicsBtn').onclick = () => {
      callAI('/api/extract-topics', 'topics', (markdown) => renderTopics(markdown));
    };

    // Quiz
    document.getElementById('generateQuizBtn').onclick = () => {
      callAI('/api/generate-quiz', 'quiz', (quizData) => renderQuiz(quizData));
    };

    // Mindmap
    document.getElementById('generateMindmapBtn').onclick = () => {
      callAI('/api/generate-mindmap', 'mindmap', async (mermaidText) => await renderMindmap(mermaidText));
    };

    // Generation Overlay Logic
    let isGenerationActive = false;

    function setGenerationProgress(percent, msg) {
        if (!isGenerationActive) return;
        const pBar = document.getElementById('generationProgressBar');
        const pText = document.getElementById('generationProgressText');
        const pMsg = document.getElementById('generationMessage');
        
        if (pBar) pBar.style.width = percent + '%';
        if (pText) pText.textContent = Math.floor(percent) + '%';
        if (msg && pMsg) {
            // Include retrying text if it exists
            const currentMsg = pMsg.textContent;
            if (currentMsg.includes('(Retrying')) {
                const retryText = currentMsg.match(/\(Retrying.*\)/)[0];
                pMsg.textContent = msg + " " + retryText;
            } else {
                pMsg.textContent = msg;
            }
        }
    }

    function startGenerationOverlay(initialMsg) {
        isGenerationActive = true;
        document.getElementById('generationOverlay').style.display = 'flex';
        
        const pBar = document.getElementById('generationProgressBar');
        if (pBar) pBar.style.transition = 'width 0.3s ease-out';
        
        setGenerationProgress(0, initialMsg || "Analyzing document...");
    }

    function stopGenerationOverlay() {
        if (!isGenerationActive) return;
        setGenerationProgress(100, "Finalizing...");
        
        setTimeout(() => {
            const overlay = document.getElementById('generationOverlay');
            if (overlay) overlay.style.display = 'none';
            isGenerationActive = false;
        }, 500);
    }