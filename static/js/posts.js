// AI Explanation butonu için click handler
document.querySelectorAll('.explain-ai-btn').forEach(button => {
    button.addEventListener('click', async function() {
        const postId = this.dataset.postId;
        const explanationDiv = document.querySelector(`#explanation-${postId}`);
        
        // Butonu devre dışı bırak
        this.disabled = true;
        
        try {
            // Loading göster
            explanationDiv.innerHTML = `
                <div class="loading">
                    <div class="spinner-border spinner-border-sm" role="status">
                        <span class="visually-hidden">Loading...</span>
                    </div>
                    <span class="ms-2">Generating explanation...</span>
                </div>
            `;
            
            // API isteği
            const response = await fetch(`/posts/${postId}/explain/`);
            const data = await response.json();
            
            if (data.explanation) {
                explanationDiv.innerHTML = `
                    <div class="explanation">
                        <div class="explanation-text">${data.explanation}</div>
                        <div class="explanation-meta">
                            <span class="source">🤖 AI Generated</span>
                        </div>
                    </div>
                `;
            } else {
                throw new Error(data.error || 'Failed to generate explanation');
            }
            
        } catch (error) {
            console.error('Error:', error);
            explanationDiv.innerHTML = `
                <div class="error">
                    <p>${error.message || 'An error occurred'}</p>
                    <button class="btn btn-sm btn-outline-primary mt-2" onclick="document.querySelector('[data-post-id=\\'${postId}\\']').click()">
                        Try Again
                    </button>
                </div>
            `;
        } finally {
            // Butonu tekrar aktif et
            this.disabled = false;
        }
    });
}); 