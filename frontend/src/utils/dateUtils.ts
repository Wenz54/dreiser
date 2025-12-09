/**
 * Date utilities for handling UTC timestamps from backend
 */

/**
 * Парсит UTC timestamp от backend и конвертирует в local Date
 * Backend возвращает UTC без 'Z', например: "2025-10-23 21:40:19.462254"
 */
export const parseBackendDate = (dateString: string | null | undefined): Date | null => {
  if (!dateString) return null;
  
  // Если уже есть 'Z' - просто парсим
  if (dateString.endsWith('Z')) {
    return new Date(dateString);
  }
  
  // Если формат ISO (с T) - добавляем Z
  if (dateString.includes('T')) {
    return new Date(dateString + 'Z');
  }
  
  // Если формат "YYYY-MM-DD HH:MM:SS" - заменяем пробел на T и добавляем Z
  const isoString = dateString.replace(' ', 'T') + 'Z';
  return new Date(isoString);
};

/**
 * Форматирует дату в локальную строку
 */
export const formatLocalDateTime = (dateString: string | null | undefined): string => {
  const date = parseBackendDate(dateString);
  if (!date) return '-';
  
  return date.toLocaleString('ru-RU', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
  });
};

/**
 * Форматирует дату в короткую локальную строку
 */
export const formatLocalDate = (dateString: string | null | undefined): string => {
  const date = parseBackendDate(dateString);
  if (!date) return '-';
  
  return date.toLocaleDateString('ru-RU', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
  });
};
