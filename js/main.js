console.log("main.js loaded");

document.addEventListener('htmx:beforeRequest', function(event) {
    console.log('htmx:beforeRequest triggered');

    if (event.detail.elt.id === 'generate-button') {
        console.log('Disabling generate button');
        event.detail.elt.disabled = true;
    }
});

document.addEventListener('htmx:afterRequest', function(event) {
    console.log('htmx:afterRequest triggered');

    if (event.detail.elt.id === 'generate-button') {
        console.log('Enabling generate button');
        event.detail.elt.disabled = false;
    }
});

document.addEventListener('DOMContentLoaded', function() {
    console.log('DOM fully loaded and parsed');
    const generateButton = document.getElementById('generate-button');
    if (generateButton) {
        console.log('Generate button found');
        generateButton.addEventListener('click', function() {
            console.log('Generate button clicked');
        });
    } else {
        console.log('Generate button not found');
    }
});

// Remove the initializeButtons function and related code since we're not using it anymore

function handleCopyClick(event) {
  const button = event.target.closest('.icon-button.copy-button');
  if (!button) return;

  console.log("Copy button clicked");

  const codeContainer = button.closest(".code-container");
  if (!codeContainer) {
    console.error("Code container not found");
    return;
  }

  const codeElement = codeContainer.querySelector("code");
  if (!codeElement) {
    console.error("Code element not found");
    return;
  }

  const codeContents = codeElement.textContent;
  const copiedText = codeContainer.querySelector("#copied-text");

  navigator.clipboard.writeText(codeContents)
    .then(() => {
      console.log("Copy successful");
      showActionText("Copied!");
    })
    .catch(error => {
      console.error("Copy failed:", error);
    });
}

function handleRegenerateClick(event) {
  const button = event.target.closest('.icon-button.regenerate-button');
  if (!button) return;

  console.log("Regenerate button clicked");
  showActionText("Regenerating...");
  // The actual regeneration is handled by HTMX
}

function showActionText(text) {
  const actionText = document.getElementById('action-text');
  if (actionText) {
    actionText.textContent = text;
    actionText.style.opacity = "1";
    if (text !== "Regenerating...") {
      setTimeout(() => {
        actionText.style.opacity = "0";
      }, 2000);
    }
  }
}

function initializeButtons() {
  const copyButtons = document.querySelectorAll(".icon-button.copy-button");
  const regenerateButtons = document.querySelectorAll(".icon-button.regenerate-button");

  console.log("Copy buttons found:", copyButtons.length);
  console.log("Regenerate buttons found:", regenerateButtons.length);

  copyButtons.forEach((button, index) => {
    console.log(`Adding listener to copy button ${index}`);
    button.removeEventListener("click", handleCopyClick);
    button.addEventListener("click", handleCopyClick);
  });

  regenerateButtons.forEach((button, index) => {
    console.log(`Adding listener to regenerate button ${index}`);
    button.removeEventListener("click", handleRegenerateClick);
    button.addEventListener("click", handleRegenerateClick);
  });
}

function setupObserver() {
  const observer = new MutationObserver((mutations) => {
    mutations.forEach((mutation) => {
      if (mutation.type === 'childList') {
        initializeButtons();
      }
    });
  });

  observer.observe(document.body, { childList: true, subtree: true });
}

function isValidGithubUrl(url) {
  const pattern = /^https?:\/\/github\.com\/[\w-]+\/[\w.-]+\/?$/;
  return pattern.test(url);
}

function validateRepoUrl() {
  const input = document.querySelector('input[name="repo_url"]');
  const errorDiv = document.getElementById('url-error');
  const generateButton = document.getElementById('generate-button');

  if (input.value.trim() === '') {
      errorDiv.textContent = 'Please enter a GitHub repository URL.';
      generateButton.disabled = true;
      return false;
  }

  if (!isValidGithubUrl(input.value)) {
      errorDiv.textContent = 'Please enter a valid GitHub repository URL.';
      generateButton.disabled = true;
      return false;
  }

  errorDiv.textContent = '';
  generateButton.disabled = false;
  return true;
}

document.addEventListener('DOMContentLoaded', function() {
  const repoUrlInput = document.querySelector('input[name="repo_url"]');
  repoUrlInput.addEventListener('input', validateRepoUrl);

  const generateForm = document.getElementById('generate-form');
  generateForm.addEventListener('submit', function(event) {
      if (!validateRepoUrl()) {
          event.preventDefault();
      }
  });

  document.body.addEventListener('click', (event) => {
    handleCopyClick(event);
    handleRegenerateClick(event);
  });

  initializeButtons();
  setupObserver();
});

