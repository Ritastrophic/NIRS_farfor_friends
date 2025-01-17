const links = document.querySelectorAll('header a');

links.forEach(link => {
  link.addEventListener('mouseover', () => {
    link.style.fontSize = '22px';
  });
  
  link.addEventListener('mouseout', () => {
    link.style.fontSize = '20px';
  });
});