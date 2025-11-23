// src/components/common/VirtualScrollList.tsx
import { memo, useCallback, useEffect, useRef, useState } from 'react';

interface VirtualScrollListProps<T> {
    items: T[];
    renderItem: (item: T, index: number) => React.ReactNode;
    itemHeight: number;
    containerHeight: number;
    getItemKey: (item: T, index: number) => string | number;
    overscan?: number;
}

const VirtualScrollList = memo(<T,>({
                                        items,
                                        renderItem,
                                        itemHeight,
                                        containerHeight,
                                        getItemKey,
                                        overscan = 5
                                    }: VirtualScrollListProps<T>) => {
    const [scrollTop, setScrollTop] = useState(0);
    const containerRef = useRef<HTMLDivElement>(null);

    // calculate which items are visible
    const startIndex = Math.max(0, Math.floor(scrollTop / itemHeight) - overscan);
    const endIndex = Math.min(
        items.length - 1,
        Math.ceil((scrollTop + containerHeight) / itemHeight) + overscan
    );

    const visibleItems = items.slice(startIndex, endIndex + 1);

    const handleScroll = useCallback((e: React.UIEvent<HTMLDivElement>) => {
        setScrollTop(e.currentTarget.scrollTop);
    }, []);

    return (
        <div
            ref={containerRef}
            className="overflow-auto"
            style={{ height: containerHeight }}
            onScroll={handleScroll}
        >
            <div style={{ height: items.length * itemHeight, position: 'relative' }}>
                {visibleItems.map((item, index) => (
                    <div
                        key={getItemKey(item, startIndex + index)}
                        style={{
                            position: 'absolute',
                            top: (startIndex + index) * itemHeight,
                            left: 0,
                            right: 0,
                            height: itemHeight,
                        }}
                    >
                        {renderItem(item, startIndex + index)}
                    </div>
                ))}
            </div>
        </div>
    );
}) as <T>(props: VirtualScrollListProps<T>) => React.ReactElement;

export default VirtualScrollList;