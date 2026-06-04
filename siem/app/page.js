'use client';

import { useEffect, useState } from 'react';

export default function PaginaInicial() {
  const [dados, setDados] = useState(null);
  const [carregando, setCarregando] = useState(true);

  const buscarDados = async () => {
    try {
      const res = await fetch('http://localhost:8090/api/log');
      const json = await res.json();
      setDados(json);
      setCarregando(false);
    } catch (e) {
      setCarregando(false);
    }
  };

  useEffect(() => {
    buscarDados();
    const intervalo = setInterval(buscarDados, 2000);
    return () => clearInterval(intervalo);
  }, []);

  const temAtaque = dados?.ataques?.length > 0;
  const temAmbulancia = dados?.ambulancia_ativa?.dados?.sirene_ativa;

  return (
    <div>
      <header className="cabecalho">
        <div>
          <h1>SmartTraffic SIEM</h1>
          <div style={{ fontSize: 10, color: '#8b949e', marginTop: 2 }}>
            Monitoramento de Seguranca IoT — STSP v1.0
          </div>
        </div>
        <div className="controles-topo">
          <div className="indicador">
            <span className="status-dot online" />
            Servidor Ativo
          </div>
          <div className="indicador">
            <span className={`status-dot ${temAmbulancia ? 'emergencia' : 'online'}`} />
            {temAmbulancia ? 'EMERGENCIA' : 'Normal'}
          </div>
          <div className="indicador">
            <span className={`status-dot ${temAtaque ? 'ataque' : 'online'}`} />
            {temAtaque ? `${dados.ataques.length} Ataques` : 'Sem ataques'}
          </div>
          <div style={{ color: '#484f58' }}>
            {dados ? `${dados.total} eventos` : '...'}
          </div>
        </div>
      </header>

      {temAmbulancia && dados.ambulancia_ativa && (
        <div style={{ padding: '8px 24px 0' }}>
          <div className="ambulancia-banner">
            <div>
              <div className="amb-info">
                AMBULANCIA EM TRANSITO — {dados.ambulancia_ativa.dados?.device_id || 'AMBULANCIA_E1'}
              </div>
              <div className="amb-coord">
                Vel: {dados.ambulancia_ativa.dados?.velocidade || '?'} km/h |
                Dir: {dados.ambulancia_ativa.dados?.direcao || '?'} |
                ({dados.ambulancia_ativa.dados?.latitude?.toFixed(4) || '?'},
                {' '}{dados.ambulancia_ativa.dados?.longitude?.toFixed(4) || '?'})
              </div>
            </div>
            <div style={{ fontSize: 24 }}>🚑</div>
          </div>
        </div>
      )}

      <main className="conteudo">
        <div className="painel" style={{ gridRow: 'span 1' }}>
          <div className="painel-titulo">
            Dispositivos (Semaforos)
            <span className="contagem">
              {Object.keys(dados?.dispositivos || {}).length} ativos
            </span>
          </div>
          <div className="dispositivos-grid">
            {['SEMAFORO_A1', 'SEMAFORO_B2'].map(id => {
              const d = dados?.dispositivos?.[id];
              const cls = !d ? '' :
                d.dados?.modo === 'EMERGENCIA' ? 'emergencia' :
                d.dados?.modo === 'MANUTENCAO' ? 'manutencao' : 'autentico';
              return (
                <div key={id} className={`cartao-dispositivo ${cls}`}>
                  <div className="cartao-nome">{id}</div>
                  <div className="cartao-info">
                    <span>Estado</span><strong>{d?.dados?.estado || '---'}</strong>
                    <span>Carros</span><strong>{d?.dados?.carros ?? '---'}</strong>
                    <span>Fila</span><strong>{d?.dados?.fila_metros ?? '---'}m</strong>
                    <span>Fase</span><strong>{d?.dados?.tempo_fase_seg ?? '---'}s</strong>
                    <span>Modo</span>
                    <strong className={d?.dados?.modo === 'EMERGENCIA' ? 'modo-emergencia' : ''}>
                      {d?.dados?.modo || '---'}
                    </strong>
                    <span>Local</span><strong>{d?.dados?.local || '---'}</strong>
                    <span>MAC</span><strong style={{ fontSize: 10 }}>
                      {d?.mac ? d.mac.substring(0, 14) + '...' : '---'}
                    </strong>
                    <span>Seguranca</span>
                    <strong style={{ color: d?.autentico ? '#3fb950' : '#f85149' }}>
                      {d?.autentico ? 'OK' : 'FALHA'}
                    </strong>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        <div className="painel">
          <div className="painel-titulo">
            Alertas de Seguranca (MitM / Intrusao)
            <span className="contagem" style={{ color: temAtaque ? '#f85149' : '#8b949e' }}>
              {dados?.ataques?.length || 0} alertas
            </span>
          </div>
          {!dados?.ataques?.length ? (
            <div className="log-vazio">Nenhum ataque detectado. Monitorando...</div>
          ) : (
            <div className="lista-ataques">
              {dados.ataques.map((a, i) => (
                <div key={i} className="alerta-mitm">
                  <span className="alerta-timestamp">{a.timestamp_servidor?.substring(11, 19)}</span>
                  <div className="alerta-tipo">
                    [{a.classificacao?.replace('MITM_', '')}] {a.device_id}
                  </div>
                  <div className="alerta-detalhe">
                    {a.mensagens?.filter(m =>
                      !m.includes('OK') && !m.includes('PERMITIDO')
                    ).join(' | ') || 'Ataque MitM detectado'}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        <div className="painel painel-cheio">
          <div className="painel-titulo">
            Log de Eventos (JSONL)
            <span className="contagem">
              Ultimos {dados?.entradas?.length || 0} eventos
            </span>
          </div>
          {!dados?.entradas?.length ? (
            <div className="log-vazio">Aguardando eventos do servidor...</div>
          ) : (
            <div style={{ maxHeight: 400, overflowY: 'auto' }}>
              <table className="tabela-log">
                <thead>
                  <tr>
                    <th>Hora</th>
                    <th>Tipo</th>
                    <th>Device ID</th>
                    <th>Estado</th>
                    <th>Modo</th>
                    <th>Hash</th>
                    <th>Assin.</th>
                    <th>MAC</th>
                    <th>Classificacao</th>
                  </tr>
                </thead>
                <tbody>
                  {dados.entradas.map((e, i) => {
                    const ehMitm = e.classificacao?.includes('MITM');
                    const ehAmb = e.tipo === 'PRESENCA_AMBULANCIA';
                    const cls = ehMitm ? 'mitm' : ehAmb ? 'ambulancia' : 'autentico';
                    return (
                      <tr key={i} className={cls}>
                        <td>{e.timestamp_servidor?.substring(11, 19) || '--:--:--'}</td>
                        <td>{e.tipo || 'PACOTE'}</td>
                        <td>{e.device_id || '?'}</td>
                        <td>{ehAmb ? '---' : e.dados?.estado || '?'}</td>
                        <td>{ehAmb ? (e.dados?.sirene_ativa ? 'SIRENE' : 'NORMAL') : e.dados?.modo || '?'}</td>
                        <td>{e.integridade_ok !== undefined ? (e.integridade_ok ? 'OK' : 'FALHA') : '---'}</td>
                        <td>{e.assinatura_ok !== undefined ? (e.assinatura_ok ? 'OK' : 'FALHA') : '---'}</td>
                        <td>{e.mac ? 'OK' : ehAmb ? '---' : 'N/D'}</td>
                        <td>{e.classificacao || e.tipo || '?'}</td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </main>
    </div>
  );
}
