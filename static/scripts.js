function today() {
  const thisday = new Date();
  const year = thisday.getFullYear();
  const month = String(thisday.getMonth() + 1).padStart(2, '0');
  const day = String(thisday.getDate()).padStart(2, '0');
  return `${year}-${month}-${day}`;
}

function rn() {
  const now = new Date();
  const hours = String(now.getHours()).padStart(2, '0');
  const minutes = String(now.getMinutes()).padStart(2, '0');
  return `${hours}:${minutes}`;
}

function populate(where, value) {
  document.getElementById(where).value = value;
}
