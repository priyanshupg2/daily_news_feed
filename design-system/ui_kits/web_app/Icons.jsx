/* global React */
// Outline icons — currentColor, 1.6 stroke. Lucide-style.

function SvgWrap({ size = 16, children, ...rest }) {
  return (
    <svg
      width={size} height={size} viewBox="0 0 24 24"
      fill="none" stroke="currentColor"
      strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round"
      className="icon" {...rest}
    >{children}</svg>
  );
}

function Icon({ name, size = 16, ...rest }) {
  switch (name) {
    case 'brief':    return <SvgWrap size={size} {...rest}><path d="M5 4h14a1 1 0 0 1 1 1v15l-4-2-3 2-2-2-3 2-4-2V5a1 1 0 0 1 1-1z"/><path d="M8 9h8M8 13h6"/></SvgWrap>;
    case 'raw':      return <SvgWrap size={size} {...rest}><line x1="3" y1="6" x2="21" y2="6"/><line x1="3" y1="12" x2="21" y2="12"/><line x1="3" y1="18" x2="21" y2="18"/><circle cx="6" cy="6" r="1"/><circle cx="6" cy="12" r="1"/><circle cx="6" cy="18" r="1"/></SvgWrap>;
    case 'profile':  return <SvgWrap size={size} {...rest}><circle cx="12" cy="8" r="4"/><path d="M4 21v-1c0-4 4-6 8-6s8 2 8 6v1"/></SvgWrap>;
    case 'search':   return <SvgWrap size={size} {...rest}><circle cx="11" cy="11" r="7"/><path d="M21 21l-4.3-4.3"/></SvgWrap>;
    case 'plus':     return <SvgWrap size={size} {...rest}><path d="M12 5v14M5 12h14"/></SvgWrap>;
    case 'arrow':    return <SvgWrap size={size} {...rest}><path d="M5 12h14M13 5l7 7-7 7"/></SvgWrap>;
    case 'bookmark': return <SvgWrap size={size} {...rest}><path d="M19 21l-7-5-7 5V5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2z"/></SvgWrap>;
    case 'sliders':  return <SvgWrap size={size} {...rest}><line x1="4" y1="6" x2="14" y2="6"/><line x1="18" y1="6" x2="20" y2="6"/><circle cx="16" cy="6" r="2"/><line x1="4" y1="12" x2="6" y2="12"/><line x1="10" y1="12" x2="20" y2="12"/><circle cx="8" cy="12" r="2"/><line x1="4" y1="18" x2="14" y2="18"/><line x1="18" y1="18" x2="20" y2="18"/><circle cx="16" cy="18" r="2"/></SvgWrap>;
    case 'mute':     return <SvgWrap size={size} {...rest}><path d="M11 5L6 9H2v6h4l5 4z"/><line x1="22" y1="9" x2="16" y2="15"/><line x1="16" y1="9" x2="22" y2="15"/></SvgWrap>;
    case 'sparkle':  return <SvgWrap size={size} {...rest}><path d="M12 3v4M12 17v4M3 12h4M17 12h4M5.6 5.6l2.8 2.8M15.6 15.6l2.8 2.8M5.6 18.4l2.8-2.8M15.6 8.4l2.8-2.8"/></SvgWrap>;
    case 'check':    return <SvgWrap size={size} {...rest}><path d="M5 12l5 5L20 7"/></SvgWrap>;
    case 'chevron':  return <SvgWrap size={size} {...rest}><path d="M9 6l6 6-6 6"/></SvgWrap>;
    case 'lens':     return <SvgWrap size={size} {...rest}><circle cx="11" cy="11" r="7"/><circle cx="11" cy="11" r="3"/><path d="M21 21l-4.3-4.3"/></SvgWrap>;
    default: return null;
  }
}

function ThumbsIcon({ direction = 'up', size = 14 }) {
  return direction === 'up' ? (
    <SvgWrap size={size}>
      <path d="M7 11v8a2 2 0 0 0 2 2h7.5a2 2 0 0 0 1.95-1.55l1.4-6A2 2 0 0 0 17.9 11H14V6a2 2 0 0 0-2-2l-3 7"/>
      <path d="M3 11h4v10H3z"/>
    </SvgWrap>
  ) : (
    <SvgWrap size={size}>
      <path d="M17 13V5a2 2 0 0 0-2-2H7.5a2 2 0 0 0-1.95 1.55l-1.4 6A2 2 0 0 0 6.1 13H10v5a2 2 0 0 0 2 2l3-7"/>
      <path d="M21 13h-4V3h4z"/>
    </SvgWrap>
  );
}

Object.assign(window, { Icon, ThumbsIcon, SvgWrap });
