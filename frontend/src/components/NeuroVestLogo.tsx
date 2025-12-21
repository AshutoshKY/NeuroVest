import React from 'react';

export const NeuroVestLogo = ({ className = "w-12 h-12" }: { className?: string }) => (
    <svg
        xmlns="http://www.w3.org/2000/svg"
        viewBox="0 0 200 200"
        fill="none"
        className={className}
        aria-label="NeuroVest Logo"
    >
        <defs>
            <linearGradient id="neuroGradient" x1="0%" y1="100%" x2="100%" y2="0%">
                <stop offset="0%" stopColor="#a855f7" />
                <stop offset="100%" stopColor="#06b6d4" />
            </linearGradient>

            <path id="arrowPath" d="M65 155 L145 55 M115 55 L145 55 L145 85"
                strokeLinecap="round" strokeLinejoin="round" />

            <mask id="arrowMask">
                <rect width="100%" height="100%" fill="white" />
                <use href="#arrowPath" stroke="black" strokeWidth="18" fill="none" />
            </mask>
        </defs>

        <g mask="url(#arrowMask)" stroke="url(#neuroGradient)" strokeWidth="12" strokeLinecap="round">
            <path d="M90 35 
               C70 35 50 45 45 70
               C40 85 45 95 40 105
               C35 120 50 140 65 145
               C80 150 90 135 90 120"/>

            <path d="M110 35
               C130 35 150 45 155 70
               C160 85 155 95 160 105
               C165 120 150 140 135 145
               C120 150 110 135 110 120"/>

            <path d="M95 50 L95 110 M105 50 L105 110" />
        </g>

        <use href="#arrowPath" stroke="url(#neuroGradient)" strokeWidth="12" fill="none" />

    </svg>
);
