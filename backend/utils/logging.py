import logging
import logging.handlers
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional
from pydantic.fields import FieldInfo
import json
from core.config import settings

class CustomEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, FieldInfo):
            return str(o)  # Or handle specifically, e.g., o.default
        return super().default(o)

class JSONFormatter(logging.Formatter):
    def format(self, record):
        log_entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno,
            'service': 'rag-chatbot',
            'environment': getattr(settings, 'ENVIRONMENT', 'development')
        }
        
        if hasattr(record, 'request_id'):
            log_entry['request_id'] = record.request_id
        if hasattr(record, 'user_id'):
            log_entry['user_id'] = record.user_id
        if hasattr(record, 'endpoint'):
            log_entry['endpoint'] = record.endpoint
        
        if record.exc_info:
            log_entry['exception'] = self.formatException(record.exc_info)
        
        import json
        return json.dumps(log_entry, ensure_ascii=False,cls=CustomEncoder)


class ContextFilter(logging.Filter):    
    def filter(self, record: logging.LogRecord) -> bool:
        record.pid = os.getpid()
        record.thread_id = record.thread
        
        if hasattr(record, 'name'):
            record.module_name = record.name.split('.')[-1]
        
        return True


class RequestContextFilter(logging.Filter):    
    def filter(self, record: logging.LogRecord) -> bool:
        if not hasattr(record, 'request_id'):
            record.request_id = None
        if not hasattr(record, 'user_id'):
            record.user_id = None
        if not hasattr(record, 'endpoint'):
            record.endpoint = None
        
        return True


class PerformanceLogger:    
    def __init__(self):
        self.logger = logging.getLogger('performance')
        self.logger.setLevel(logging.INFO)
    
    def log_request_duration(self, endpoint: str, method: str, duration: float, status_code: int) -> None:
        self.logger.info(
            f"Request {method} {endpoint} completed in {duration:.3f}s with status {status_code}",
            extra={
                'event_type': 'request_duration',
                'endpoint': endpoint,
                'method': method,
                'duration_ms': round(duration * 1000, 2),
                'status_code': status_code
            }
        )
    
    def log_rag_performance(self, query: str, retrieval_time: float, generation_time: float, 
                           total_time: float, num_sources: int) -> None:
        self.logger.info(
            f"RAG query processed in {total_time:.3f}s (retrieval: {retrieval_time:.3f}s, generation: {generation_time:.3f}s)",
            extra={
                'event_type': 'rag_performance',
                'query_length': len(query),
                'retrieval_time_ms': round(retrieval_time * 1000, 2),
                'generation_time_ms': round(generation_time * 1000, 2),
                'total_time_ms': round(total_time * 1000, 2),
                'num_sources': num_sources
            }
        )
    
    def log_embedding_performance(self, text_length: int, embedding_time: float, 
                                 embedding_dimension: int) -> None:
        self.logger.info(
            f"Embedding generated for {text_length} chars in {embedding_time:.3f}s",
            extra={
                'event_type': 'embedding_performance',
                'text_length': text_length,
                'embedding_time_ms': round(embedding_time * 1000, 2),
                'embedding_dimension': embedding_dimension
            }
        )


class SecurityLogger:    
    def __init__(self):
        self.logger = logging.getLogger('security')
        self.logger.setLevel(logging.INFO)
    
    def log_login_attempt(self, email: str, success: bool, ip_address: str) -> None:
        status = "successful" if success else "failed"
        self.logger.info(
            f"Login attempt {status} for {email} from {ip_address}",
            extra={
                'event_type': 'login_attempt',
                'email': email,
                'success': success,
                'ip_address': ip_address
            }
        )
    
    def log_failed_authentication(self, endpoint: str, ip_address: str, reason: str) -> None:
        self.logger.warning(
            f"Authentication failed for {endpoint} from {ip_address}: {reason}",
            extra={
                'event_type': 'auth_failure',
                'endpoint': endpoint,
                'ip_address': ip_address,
                'reason': reason
            }
        )
    
    def log_rate_limit_exceeded(self, ip_address: str, endpoint: str) -> None:
        self.logger.warning(
            f"Rate limit exceeded for {endpoint} from {ip_address}",
            extra={
                'event_type': 'rate_limit_exceeded',
                'ip_address': ip_address,
                'endpoint': endpoint
            }
        )


def setup_logging() -> None:    
    log_dir = Path(getattr(settings, 'LOG_DIR', 'logs'))
    log_dir.mkdir(parents=True, exist_ok=True)
    
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, getattr(settings, 'LOG_LEVEL', 'INFO').upper()))
     
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    json_formatter = JSONFormatter()
    
    console_formatter = logging.Formatter(
        fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    
    environment = getattr(settings, 'ENVIRONMENT', 'development')
    console_handler.setFormatter(console_formatter if environment == 'development' else json_formatter)
    console_handler.addFilter(ContextFilter())
    console_handler.addFilter(RequestContextFilter())
    
    file_handler = logging.handlers.RotatingFileHandler(
        filename=log_dir / 'app.log',
        maxBytes=10 * 1024 * 1024,
        backupCount=5,
        encoding="utf-8"
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(json_formatter)
    file_handler.addFilter(ContextFilter())
    file_handler.addFilter(RequestContextFilter())
    
    error_handler = logging.handlers.RotatingFileHandler(
        filename=log_dir / 'errors.log',
        maxBytes=10 * 1024 * 1024,
        backupCount=5,
        encoding="utf-8"
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(json_formatter)
    error_handler.addFilter(ContextFilter())
    
    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)
    root_logger.addHandler(error_handler)
    
    setup_specialized_loggers(log_dir, json_formatter)
    
    logging.info(f"Logging configured - Level: {getattr(settings, 'LOG_LEVEL', 'INFO')}, Environment: {settings.ENVIRONMENT}")


def setup_specialized_loggers(log_dir: Path, formatter: JSONFormatter) -> None:    
    perf_logger = logging.getLogger('performance')
    perf_handler = logging.handlers.RotatingFileHandler(
        filename=log_dir / 'performance.log',
        maxBytes=10 * 1024 * 1024,
        backupCount=3,
        encoding="utf-8"
    )
    perf_handler.setFormatter(formatter)
    perf_logger.addHandler(perf_handler)
    perf_logger.propagate = False
    
    security_logger = logging.getLogger('security')
    security_handler = logging.handlers.RotatingFileHandler(
        filename=log_dir / 'security.log',
        maxBytes=10 * 1024 * 1024,
        backupCount=5,
        encoding="utf-8"
    )
    security_handler.setFormatter(formatter)
    security_logger.addHandler(security_handler)
    security_logger.propagate = False
    
    access_logger = logging.getLogger('access')
    access_handler = logging.handlers.RotatingFileHandler(
        filename=log_dir / 'access.log',
        maxBytes=10 * 1024 * 1024,
        backupCount=3,
        encoding="utf-8"
    )
    access_handler.setFormatter(formatter)
    access_logger.addHandler(access_handler)
    access_logger.propagate = False


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)


class LoggingMiddleware:    
    def __init__(self):
        self.logger = get_logger('access')
        self.performance_logger = PerformanceLogger()
    
    async def log_request(self, request, call_next):
        start_time = datetime.utcnow()
        
        request_info = {
            'method': request.method,
            'url': str(request.url),
            'client_ip': request.client.host if request.client else None
        }
        
        response = await call_next(request)
        
        duration = (datetime.utcnow() - start_time).total_seconds()
        
        self.logger.info(
            f"{request.method} {request.url.path} - {response.status_code}",
            extra={
                'event_type': 'http_request',
                'request_info': request_info,
                'response_status': response.status_code,
                'duration_ms': round(duration * 1000, 2)
            }
        )
        
        self.performance_logger.log_request_duration(
            endpoint=request.url.path,
            method=request.method,
            duration=duration,
            status_code=response.status_code
        )
        
        return response


performance_logger = PerformanceLogger()
security_logger = SecurityLogger()


def log_exception(logger: logging.Logger, exception: Exception, context: Optional[Dict[str, Any]] = None) -> None:
    logger.error(
        f"Exception occurred: {str(exception)}",
        extra={
            'event_type': 'exception',
            'exception_type': type(exception).__name__,
            'exception_message': str(exception),
            'context': context or {}
        },
        exc_info=True
    )


def log_business_event(event_type: str, **kwargs) -> None:
    logger = get_logger('business')
    logger.info(
        f"Business event: {event_type}",
        extra={
            'event_type': event_type,
            **kwargs
        }
    )


def configure_uvicorn_logging():
    uvicorn_access = logging.getLogger("uvicorn.access")
    uvicorn_access.handlers = []
    
    uvicorn_error = logging.getLogger("uvicorn.error")
    uvicorn_error.handlers = []


if getattr(settings, 'AUTO_SETUP_LOGGING', True):
    setup_logging()

