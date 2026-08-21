import { setCurrentFile, setStatus, setDirty } from './core.js';
import { render } from './render.js';
import { importFromUrl } from './subgraph.js';
import { updateRefUI } from './selection.js';
import { updateMdUI } from './md_link.js';
import { setTool } from './interactions.js';

importFromUrl('main_agent.json')
    .then(() => {
        setCurrentFile('main_agent.json');
        updateRefUI();
        updateMdUI();
        setDirty(false);
        setStatus('Loaded main_agent.json');
    })
    .catch((err) => {
        setStatus('Autoload main_agent.json failed: ' + err.message + ' — starting blank canvas');
        render();
    });
setTool('select');