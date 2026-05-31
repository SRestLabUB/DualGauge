import { ModelData, SortKey, SortDirection } from '../types/models';
import { FilterType } from '../components/SearchSection';

export const getScoreClass = (score: number): string => {
  if (score >= 80) return 'text-academic-success';
  if (score >= 60) return 'text-academic-warning';
  return 'text-academic-error';
};

export const sortData = (
  data: ModelData[],
  key: SortKey,
  direction: SortDirection
): ModelData[] => {
  return [...data].sort((a, b) => {
    const aVal = a[key];
    const bVal = b[key];

    if (typeof aVal === 'number' && typeof bVal === 'number') {
      return direction === 'asc' ? aVal - bVal : bVal - aVal;
    } else {
      const aStr = String(aVal).toLowerCase();
      const bStr = String(bVal).toLowerCase();
      
      if (aStr < bStr) return direction === 'asc' ? -1 : 1;
      if (aStr > bStr) return direction === 'asc' ? 1 : -1;
      return 0;
    }
  });
};

export const filterData = (
  data: ModelData[],
  searchTerm: string,
  filterType: FilterType
): ModelData[] => {
  return data.filter(model => {
    const matchesSearch = model.model.toLowerCase().includes(searchTerm.toLowerCase());
    
    let matchesFilter = true;
    if (filterType !== 'all') {
      switch (filterType) {
        case 'open':
          matchesFilter = model.type === 'Open';
          break;
        case 'proprietary':
          matchesFilter = model.type === 'Proprietary';
          break;
        case 'instruction':
          matchesFilter = model.model.toLowerCase().includes('instruct') || 
                        model.model.toLowerCase().includes('chat');
          break;
        case 'base':
          matchesFilter = !model.model.toLowerCase().includes('instruct') && 
                        !model.model.toLowerCase().includes('chat');
          break;
      }
    }

    return matchesSearch && matchesFilter;
  });
};