document.addEventListener('DOMContentLoaded', function() {
    const llmSelector = document.querySelector('#llm_selector');
    if (llmSelector) {
        llmSelector.addEventListener('change', function(e) {
            const value = e.target.value;
            console.log('LLM model set to:', value);

            fetch('/api/set-llm', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ model: value })
            });
        });
    }
});
