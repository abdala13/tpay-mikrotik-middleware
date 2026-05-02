document.addEventListener('submit', (e) => {
  const btn = e.target.querySelector('button, input[type="submit"]');
  if(btn){ btn.disabled = true; btn.dataset.old = btn.value || btn.innerText; if(btn.tagName === 'INPUT') btn.value='Working...'; else btn.innerText='Working...'; }
});
