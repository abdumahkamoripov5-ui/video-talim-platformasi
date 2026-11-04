(() => {
  const form = document.getElementById('media-upload-form');
  if (!form) return;
  const kind = document.getElementById('kind');
  const fileInput = document.getElementById('file');
  const status = document.getElementById('upload-status');
  const progress = document.getElementById('upload-progress');
  const button = document.getElementById('upload-button');
  let busy = false;
  kind.addEventListener('change', () => {
    document.getElementById('course-row').hidden = kind.value !== 'thumbnail';
    document.getElementById('lesson-row').hidden = kind.value === 'thumbnail';
    fileInput.accept = {video: '.mp4', thumbnail: '.jpg,.jpeg,.png,.webp', attachment: '.pdf,.doc,.docx,.txt,.zip'}[kind.value];
    fileInput.value = '';
  });
  window.addEventListener('beforeunload', event => { if (busy) { event.preventDefault(); event.returnValue = ''; } });
  const api = async (path, data) => {
    const response = await fetch(path, {
      method: 'POST', credentials: 'same-origin',
      headers: {'Content-Type': 'application/json', 'X-CSRFToken': form.querySelector('[name=csrfmiddlewaretoken]').value},
      body: JSON.stringify(data),
    });
    const result = await response.json().catch(() => ({detail: 'Admin sessiyasi yoki server javobini tekshiring.'}));
    if (!response.ok) throw new Error(typeof result.detail === 'string' ? result.detail : JSON.stringify(result.detail));
    return result;
  };
  const duration = file => new Promise((resolve, reject) => {
    const video = document.createElement('video');
    const url = URL.createObjectURL(file);
    const cleanup = () => { clearTimeout(timer); URL.revokeObjectURL(url); video.removeAttribute('src'); video.load(); };
    const timer = setTimeout(() => { cleanup(); reject(new Error('Video ma’lumotlari o‘qilmadi. MP4 formatini tekshiring.')); }, 15000);
    video.preload = 'metadata';
    video.onloadedmetadata = () => { const seconds = video.duration; cleanup(); Number.isFinite(seconds) && seconds > 0 ? resolve(Math.ceil(seconds)) : reject(new Error('Video davomiyligi yaroqsiz.')); };
    video.onerror = () => { cleanup(); reject(new Error('Video ochilmadi. H.264/AAC MP4 fayldan foydalaning.')); };
    video.src = url;
  });
  const putFile = (url, type, file) => new Promise((resolve, reject) => {
    const xhr = new XMLHttpRequest();
    xhr.open('PUT', url);
    xhr.setRequestHeader('Content-Type', type);
    xhr.upload.onprogress = event => { if (event.lengthComputable) { progress.value = event.loaded / event.total * 100; status.textContent = `Yuklanmoqda: ${Math.round(progress.value)}%`; } };
    xhr.onload = () => xhr.status >= 200 && xhr.status < 300 ? resolve() : reject(new Error(`Fayl yuklanmadi (${xhr.status}). Saqlash ruxsatlarini tekshiring.`));
    xhr.onerror = () => reject(new Error('Saqlash xizmatiga ulanilmadi. Internet va bucket CORS sozlamalarini tekshiring.'));
    xhr.send(file);
  });
  document.getElementById('configure-storage')?.addEventListener('click', async event => {
    event.target.disabled = true;
    try { const result = await api('/admin/media-upload/configure/', {}); status.textContent = result.detail; }
    catch (error) { status.textContent = error.message; }
    finally { event.target.disabled = false; }
  });
  form.addEventListener('submit', async event => {
    event.preventDefault();
    if (busy) return;
    const file = fileInput.files[0];
    const selectedKind = kind.value;
    const target = document.getElementById(selectedKind === 'thumbnail' ? 'course' : 'lesson').value;
    if (!file || !target) { status.textContent = 'Fayl va tegishli kurs yoki darsni tanlang.'; return; }
    busy = true; button.disabled = true; progress.hidden = false; progress.value = 0;
    try {
      status.textContent = 'Yuklash tayyorlanmoqda…';
      const info = await api('/admin/media-upload/start/', {
        kind: selectedKind, target_id: Number(target), filename: file.name, size: file.size,
        title: document.getElementById('title').value,
        duration_seconds: selectedKind === 'video' ? await duration(file) : 0,
      });
      await putFile(info.url, info.content_type, file);
      status.textContent = 'Yuklandi. Fayl tekshirilib, saqlanmoqda…';
      await api(`/admin/media-upload/${info.id}/complete/`, {});
      status.textContent = 'Tayyor! Fayl muvaffaqiyatli saqlandi.';
      fileInput.value = '';
    } catch (error) { status.textContent = error.message || 'Yuklash bajarilmadi.'; }
    finally { busy = false; button.disabled = false; }
  });
})();
