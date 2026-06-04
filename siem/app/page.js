'use client';

import { useEffect, useState, useRef, useCallback } from 'react';

export default function PaginaInicial() {
  const [dados, setDados] = useState(null);
  const [colVisiveis, setColVisiveis] = useState({
    hora: true,
    tipo: true,
    device: true,
    estado: true,
    modo: true,
    hash: false,
    assinatura: false,
    mac: false,
    classificacao: true,
  });
  const [larguraEsquerda, setLarguraEsquerda] = useState(420);
  const arrastando = useRef(false);
  const divisorRef = useRef(null);

  const buscarDados = useCallback(async () => {
    try {
      const res = await fetch('http://localhost:8090/api/log');
      const json = await res.json();
      setDados(json);
    } catch (e) {}
  }, []);

  useEffect(() => {
    buscarDados();
    const intervalo = setInterval(buscarDados, 2000);
    return () => clearInterval(intervalo);
  }, [buscarDados]);

  useEffect(() => {
    const aoMover = (e) => {
      if (!arrastando.current) return;
      const nova = Math.max(280, Math.min(800, e.clientX));
      setLarguraEsquerda(nova);
    };
    const aoSoltar = () => { arrastando.current = false; };
    window.addEventListener('mousemove', aoMover);
    window.addEventListener('mouseup', aoSoltar);
    return () => {
      window.removeEventListener('mousemove', aoMover);
      window.removeEventListener('mouseup', aoSoltar);
    };
  }, []);

  const temAtaque = dados?.ataques?.length > 0;
  const temAmbulancia = dados?.ambulancia_ativa?.dados?.sirene_ativa;

  const toggleCol = (col) => {
    setColVisiveis(prev => ({ ...prev, [col]: !prev[col] }));
  };

  const ColT = ({ id, label }) => (
    <button
      className={`toggle-coluna ${colVisiveis[id] ? 'ativo' : ''}`}
      onClick={() => toggleCol(id)}
    >{label}</button>
  );

  const Luzes = ({ estado }) => (
    <div className="semaforo-luzes">
      <div className={`luz vermelha ${estado === 'VERMELHO' ? 'ativa' : ''}`} />
      <div className={`luz amarela ${estado === 'AMARELO' ? 'ativa' : ''}`} />
      <div className={`luz verde ${estado === 'VERDE' ? 'ativa' : ''}`} />
    </div>
  );

  return (
    <div>
      <header className="cabecalho">
        <div>
          <h1>SmartTraffic SIEM</h1>
          <div style={{ fontSize: 10, color: '#8b949e', marginTop: 1 }}>
            Monitoramento de Seguranca IoT &middot; STSP v1.0
          </div>
        </div>
        <div className="status-bar">
          <span><span className="status-dot online" /> Servidor Ativo</span>
          <span>
            <span className={`status-dot ${temAmbulancia ? 'emergencia' : 'online'}`} />
            {temAmbulancia ? 'Emergencia' : 'Normal'}
          </span>
          <span>
            <span className={`status-dot ${temAtaque ? 'ataque' : 'online'}`} />
            {temAtaque ? `${dados.ataques.length} ataque(s)` : 'Sem ataques'}
          </span>
          <span style={{ color: '#484f58' }}>
            {dados ? `${dados.total} eventos` : '...'}
          </span>
        </div>
      </header>

      {temAmbulancia && dados.ambulancia_ativa && (
        <div className="ambulancia-alerta">
          <div className="amb-titulo">
            <span style={{ fontSize: 20 }}>&#128657;</span>
            Ambulancia em transito
            <span style={{ fontSize: 10, fontWeight: 400, color: '#8b949e' }}>
              {dados.ambulancia_ativa.dados?.device_id || 'AMBULANCIA_E1'}
            </span>
          </div>
          <div className="amb-dados">
            <span>Vel: {dados.ambulancia_ativa.dados?.velocidade || '?'} km/h</span>
            <span>Dir: {dados.ambulancia_ativa.dados?.direcao || '?'}</span>
            <span>
              ({dados.ambulancia_ativa.dados?.latitude?.toFixed(4) || '?'},
              {dados.ambulancia_ativa.dados?.longitude?.toFixed(4) || '?'})
            </span>
          </div>
        </div>
      )}

      <div className="conteudo-principal">
        <div className="painel-esquerdo" style={{ width: larguraEsquerda }}>
          <div className="cartao-titulo" style={{ marginTop: 0, marginBottom: 0 }}>
            Dispositivos
            <span className="badge ok">
              {Object.keys(dados?.dispositivos || {}).length} ativos
            </span>
          </div>

          {['SEMAFORO_A1', 'SEMAFORO_B2'].map(id => {
            const d = dados?.dispositivos?.[id];
            const cls = !d ? '' :
              d.dados?.modo === 'EMERGENCIA' ? 'emergencia' :
              d.dados?.modo === 'MANUTENCAO' ? 'manutencao' : '';
            return (
              <div key={id} className={`semaforo-card ${cls}`}>
                <div className="semaforo-header">
                  <span className="semaforo-nome">{id}</span>
                  <span className={`semaforo-modo ${(d?.dados?.modo || 'normal').toLowerCase()}`}>
                    {d?.dados?.modo || 'N/D'}
                  </span>
                </div>
                <Luzes estado={d?.dados?.estado || 'VERMELHO'} />
                <div className="semaforo-info">
                  <span className="rotulo">Carros</span>
                  <span className="valor">{d?.dados?.carros ?? '---'}</span>
                  <span className="rotulo">Fila</span>
                  <span className="valor">{d?.dados?.fila_metros ?? '---'} m</span>
                  <span className="rotulo">Fase</span>
                  <span className="valor">{d?.dados?.tempo_fase_seg ?? '---'}s</span>
                  <span className="rotulo">Local</span>
                  <span className="valor">{d?.dados?.local || '---'}</span>
                  <span className="rotulo">MAC</span>
                  <span className="valor" style={{ fontSize: 9 }}>
                    {d?.mac ? d.mac : '---'}
                  </span>
                  <span className="rotulo">Seguranca</span>
                  <span className="valor" style={{ color: d?.autentico ? '#3fb950' : '#f85149' }}>
                    {d?.autentico ? 'Verificado' : 'Falha'}
                  </span>
                </div>
              </div>
            );
          })}

          <div className="cartao" style={{ flex: 1, overflow: 'auto', minHeight: 100 }}>
            <div className="cartao-titulo">
              Alertas de intrusao
              <span className={`badge ${temAtaque ? 'alerta' : 'ok'}`}>
                {dados?.ataques?.length || 0}
              </span>
            </div>
            {!dados?.ataques?.length ? (
              <div className="log-vazio">Nenhum ataque detectado.<br/>Monitorando...</div>
            ) : (
              dados.ataques.map((a, i) => (
                <div key={i} className="alerta-mitm">
                  <div className="alerta-tipo">
                    [{a.classificacao?.replace('MITM_', '')}] {a.device_id}
                  </div>
                  <div className="alerta-detalhe">
                    {a.timestamp_servidor?.substring(11, 19)} &middot;
                    {' '}{a.mensagens?.filter(m => !m.includes('OK') && !m.includes('PERMITIDO')).join(' ')}
                  </div>
                </div>
              ))
            )}
          </div>
        </div>

        <div
          ref={divisorRef}
          className={`divisor ${arrastando.current ? 'arrastando' : ''}`}
          onMouseDown={(e) => { e.preventDefault(); arrastando.current = true; }}
        />

        <div className="painel-direito">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
            <div className="cartao-titulo" style={{ margin: 0 }}>
              Log de eventos
              <span className="badge info" style={{ marginLeft: 8 }}>
                {dados?.entradas?.length || 0} recentes
              </span>
            </div>
            <div className="controles-visibilidade">
              <ColT id="hora" label="Hora" />
              <ColT id="tipo" label="Tipo" />
              <ColT id="device" label="Device" />
              <ColT id="estado" label="Estado" />
              <ColT id="modo" label="Modo" />
              <ColT id="hash" label="Hash" />
              <ColT id="assinatura" label="Assin." />
              <ColT id="mac" label="MAC" />
              <ColT id="classificacao" label="Classif." />
            </div>
          </div>

          {!dados?.entradas?.length ? (
            <div className="log-vazio" style={{ flex: 1 }}>
              Aguardando eventos do servidor central...
            </div>
          ) : (
            <div style={{ flex: 1, overflow: 'auto' }}>
              <table className="tabela-log">
                <thead>
                  <tr>
                    {colVisiveis.hora && <th>Hora</th>}
                    {colVisiveis.tipo && <th>Tipo</th>}
                    {colVisiveis.device && <th>Device</th>}
                    {colVisiveis.estado && <th>Estado</th>}
                    {colVisiveis.modo && <th>Modo</th>}
                    {colVisiveis.hash && <th>Hash</th>}
                    {colVisiveis.assinatura && <th>Assin.</th>}
                    {colVisiveis.mac && <th>MAC</th>}
                    {colVisiveis.classificacao && <th>Classificacao</th>}
                  </tr>
                </thead>
                <tbody>
                  {dados.entradas.map((e, i) => {
                    const ehMitm = e.classificacao?.includes('MITM') ||
                                   e.classificacao === 'DISPOSITIVO_NAO_CADASTRADO';
                    const ehAmb = e.tipo === 'PRESENCA_AMBULANCIA';
                    const cls = ehMitm ? 'mitm' : ehAmb ? 'ambulancia' : 'autentico';
                    return (
                      <tr key={i} className={cls}>
                        {colVisiveis.hora && <td>{e.timestamp_servidor?.substring(11, 19) || '--:--:--'}</td>}
                        {colVisiveis.tipo && <td>{e.tipo || 'PACOTE'}</td>}
                        {colVisiveis.device && <td>{e.device_id || '?'}</td>}
                        {colVisiveis.estado && (
                          <td>
                            {ehAmb ? '---' : (
                              <span className="coluna-check">
                                <span style={{
                                  display: 'inline-block', width: 8, height: 8, borderRadius: '50%',
                                  background: e.dados?.estado === 'VERDE' ? '#3fb950' :
                                              e.dados?.estado === 'AMARELO' ? '#d29922' :
                                              e.dados?.estado === 'VERMELHO' ? '#f85149' : '#484f58'
                                }} />
                                {e.dados?.estado || '?'}
                              </span>
                            )}
                          </td>
                        )}
                        {colVisiveis.modo && (
                          <td>{ehAmb ? (e.dados?.sirene_ativa ? 'Sirene' : 'Normal') : e.dados?.modo || '?'}</td>
                        )}
                        {colVisiveis.hash && (
                          <td className="coluna-check">
                            {e.integridade_ok !== undefined ? (
                              <span className={e.integridade_ok ? 'ico-ok' : 'ico-falha'}>
                                {e.integridade_ok ? '\u2713' : '\u2717'}
                              </span>
                            ) : '---'}
                          </td>
                        )}
                        {colVisiveis.assinatura && (
                          <td className="coluna-check">
                            {e.assinatura_ok !== undefined ? (
                              <span className={e.assinatura_ok ? 'ico-ok' : 'ico-falha'}>
                                {e.assinatura_ok ? '\u2713' : '\u2717'}
                              </span>
                            ) : '---'}
                          </td>
                        )}
                        {colVisiveis.mac && (
                          <td className="coluna-check">
                            {e.mac_ok !== undefined ? (
                              <span className={e.mac_ok ? 'ico-ok' : 'ico-falha'}>
                                {e.mac_ok ? '\u2713' : '\u2717'}
                              </span>
                            ) : (ehAmb ? '---' : '---')}
                          </td>
                        )}
                        {colVisiveis.classificacao && <td>{e.classificacao || e.tipo || '?'}</td>}
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
