import sys
import re
path = r'd:\- E -\CONTINENTAL\10° CICLO\Albañilería\Unidad I\C1\12-PA2-consolidado2-analisis-diseno-confinada\dibujo\generar_visor_3d.py'
with open(path, 'r', encoding='utf-8') as f:
    c = f.read()

c = c.replace('let hoveredMesh = null;', 'let muroSeleccionadoInfo = null;\n    let hoveredMesh = null;')

c = c.replace('function mostrarDatosParapeto(u) {{', 'function mostrarDatosParapeto(u) {{\n      document.getElementById(\'btn-explain\').style.display = \'none\';')
c = c.replace('function mostrarDatosEscalera(u) {{', 'function mostrarDatosEscalera(u) {{\n      document.getElementById(\'btn-explain\').style.display = \'none\';')
c = c.replace('function mostrarDatosAmbiente(u) {{', 'function mostrarDatosAmbiente(u) {{\n      document.getElementById(\'btn-explain\').style.display = \'none\';')
c = c.replace('function mostrarDatosTabique(u) {{', 'function mostrarDatosTabique(u) {{\n      document.getElementById(\'btn-explain\').style.display = \'none\';')
c = c.replace('function mostrarDatosCimiento(u) {{', 'function mostrarDatosCimiento(u) {{\n      document.getElementById(\'btn-explain\').style.display = \'none\';')
c = c.replace('function mostrarDatosSobrecimiento(u) {{', 'function mostrarDatosSobrecimiento(u) {{\n      document.getElementById(\'btn-explain\').style.display = \'none\';')
c = c.replace('function mostrarDatosMuro(m, tipoCol) {{', 'function mostrarDatosMuro(m, tipoCol) {{\n      muroSeleccionadoInfo = m;\n      document.getElementById(\'btn-explain\').style.display = \'block\';')

fn_explain = '''
    function mostrarExplicacionE070() {{
      if(!muroSeleccionadoInfo) return;
      const m = muroSeleccionadoInfo;
      const Vm = m.Vm.toFixed(1);
      const Ve = m.Ve_mod.toFixed(1);
      const lim = m.lim_852.toFixed(1);
      const ok = (parseFloat(Ve) <= parseFloat(lim)) ? '<span style="color:#10b981">CUMPLE</span>' : '<span style="color:#ef4444">NO CUMPLE</span>';
      
      const html = `
        <div style="margin-bottom:8px;"><span style="color:#38bdf8;">Demanda Sísmica (Ve):</span> <span style="color:#f1f5f9">${{Ve}} kgf</span> <br><span style="color:#94a3b8; font-size:0.75rem;">(Cortante Sismo Moderado OpenSeesPy)</span></div>
        <div style="margin-bottom:8px;"><span style="color:#38bdf8;">Capacidad Analítica (Vm):</span> <span style="color:#f1f5f9">${{Vm}} kgf</span></div>
        <hr style="border-color:rgba(255,255,255,0.1); margin:8px 0;">
        <div style="font-size:0.85rem; margin-bottom:4px; color:#f59e0b;">Fórmula Reglamentaria:</div>
        <div style="background:#1e293b; padding:8px; border-radius:6px; font-size:0.95rem; text-align:center; border:1px solid rgba(255,255,255,0.1);">
          <strong>V<sub>e</sub> &le; 0.55 &times; V<sub>m</sub></strong>
        </div>
        <div style="margin-top:10px; font-size:0.95rem; text-align:center;">
          ${{Ve}} &le; 0.55 &times; ${{Vm}} <br>
          ${{Ve}} &le; ${{lim}} &rarr; <strong>${{ok}}</strong>
        </div>
        <div style="margin-top:12px; font-size:0.7rem; color:#94a3b8; line-height:1.4;">
          * Según el Artículo 8.5.2 de la E.070, si la demanda por sismo moderado supera el 55% de la resistencia nominal, el muro corre riesgo de fisuración severa y debe reforzarse o engrosarse.
        </div>
      `;
      document.getElementById('modal-formula-content').innerHTML = html;
      document.getElementById('modal-explain').style.display = 'block';
    }}

    function onWindowResize() {{'''

c = c.replace('function onWindowResize() {{', fn_explain)

with open(path, 'w', encoding='utf-8') as f:
    f.write(c)
print("Fix successfully applied.")
