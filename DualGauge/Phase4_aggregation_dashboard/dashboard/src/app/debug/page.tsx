'use client';

import React from 'react';

export default function DebugPage() {
  return (
    <div style={{ 
      margin: 0, 
      padding: 0, 
      minHeight: '100vh',
      backgroundColor: '#f8fafc',
      color: '#1e293b',
      width: '100%'
    }}>
      {/* Navbar */}
      <nav style={{
        width: '100%',
        background: 'linear-gradient(to right, #0f172a, #1e40af, #0f172a)',
        borderBottom: '1px solid rgba(5, 150, 105, 0.2)',
        position: 'sticky',
        top: 0,
        zIndex: 50
      }}>
        <div style={{
          maxWidth: '80rem',
          margin: '0 auto',
          padding: '0 1.5rem',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          height: '5rem'
        }}>
          <div style={{
            fontSize: '1.875rem',
            fontWeight: 'bold',
            background: 'linear-gradient(to right, #3b82f6, #1e40af)',
            backgroundClip: 'text',
            WebkitBackgroundClip: 'text',
            color: 'transparent'
          }}>
            🤗 Leaderboard
          </div>
          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: '3rem'
          }}>
            <a href="#" style={{
              display: 'flex',
              alignItems: 'center',
              gap: '0.5rem',
              color: 'white',
              textDecoration: 'none',
              fontWeight: 500
            }}>
              <span>🏠</span><span>Home</span>
            </a>
            <a href="#" style={{
              display: 'flex',
              alignItems: 'center',
              gap: '0.5rem',
              color: 'white',
              textDecoration: 'none',
              fontWeight: 500
            }}>
              <span>📚</span><span>Models</span>
            </a>
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <div style={{
        width: '100%',
        background: 'linear-gradient(to bottom right, #f8fafc, #f1f5f9, #f8fafc)',
        padding: '3rem 1.5rem'
      }}>
        <div style={{
          maxWidth: '80rem',
          margin: '0 auto'
        }}>
          {/* Header */}
          <div style={{
            textAlign: 'center',
            marginBottom: '4rem'
          }}>
            <h1 style={{
              fontSize: '4rem',
              fontWeight: 800,
              background: 'linear-gradient(to right, #1e3a8a, #3b82f6, #1e40af)',
              backgroundClip: 'text',
              WebkitBackgroundClip: 'text',
              color: 'transparent',
              marginBottom: '1.5rem',
              lineHeight: 1.1
            }}>
              Open LLM Leaderboard
            </h1>
            <p style={{
              fontSize: '1.25rem',
              color: '#1e293b',
              maxWidth: '80rem',
              margin: '0 auto',
              lineHeight: 1.6,
              fontWeight: 300
            }}>
              A comprehensive evaluation of large language models across multiple benchmarks and tasks.
              <br />
              <span style={{ color: '#059669', fontWeight: 500 }}>Compare model performance</span>, explore capabilities, and discover the latest advances in AI.
            </p>
          </div>

          {/* Search Section */}
          <div style={{
            display: 'flex',
            flexDirection: 'column',
            justifyContent: 'center',
            alignItems: 'center',
            gap: '1.5rem',
            maxWidth: '64rem',
            margin: '0 auto 3rem auto'
          }}>
            <div style={{
              position: 'relative',
              flex: 1,
              width: '100%',
              maxWidth: '32rem'
            }}>
              <input
                type="text"
                placeholder="Search models..."
                style={{
                  display: 'block',
                  width: '100%',
                  padding: '1rem',
                  border: '1px solid #e2e8f0',
                  borderRadius: '1rem',
                  backgroundColor: 'white',
                  color: '#1e293b',
                  fontSize: '1.125rem',
                  outline: 'none'
                }}
              />
            </div>
            <div style={{ position: 'relative' }}>
              <select style={{
                display: 'block',
                width: '100%',
                padding: '1rem 1.5rem',
                border: '1px solid #e2e8f0',
                borderRadius: '1rem',
                backgroundColor: 'white',
                color: '#1e293b',
                fontSize: '1.125rem',
                minWidth: '12.5rem',
                cursor: 'pointer',
                outline: 'none'
              }}>
                <option value="all">All Models</option>
                <option value="open">Open Source</option>
                <option value="proprietary">Proprietary</option>
              </select>
            </div>
          </div>

          {/* Table Container */}
          <div style={{
            background: 'linear-gradient(to right, #f1f5f9, #f8fafc)',
            borderRadius: '1rem',
            border: '1px solid #e2e8f0',
            padding: '2rem',
            boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.25)'
          }}>
            <div style={{
              background: 'linear-gradient(to bottom right, #f1f5f9, #f8fafc)',
              borderRadius: '1rem',
              border: '1px solid #e2e8f0',
              overflow: 'hidden',
              padding: '2rem',
              textAlign: 'center'
            }}>
              <h2 style={{ fontSize: '1.5rem', marginBottom: '1rem', color: '#1e293b' }}>
                Pure CSS - Should be centered now!
              </h2>
              <p style={{ color: '#64748b' }}>
                This uses pure CSS without any Tailwind classes. Content should be perfectly centered.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}