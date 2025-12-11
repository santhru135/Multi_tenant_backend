"""
Response utilities for consistent API responses.

This module provides standardized response models and helper functions
for creating consistent API responses across the application.
"""
from typing import Any, Dict, Generic, List, Optional, TypeVar, Union
from datetime import datetime
from pydantic import BaseModel, Field
from fastapi import status
from fastapi.responses import JSONResponse
from bson import ObjectId
import json

T = TypeVar('T')

class ApiResponse(BaseModel, Generic[T]):
    """
    Base response model for all API responses.
    
    Attributes:
        success: Boolean indicating if the request was successful
        data: The response payload (optional)
        error: Error details if the request failed (optional)
        meta: Additional metadata (optional)
    """
    success: bool = Field(..., description="Indicates if the request was successful")
    data: Optional[T] = Field(None, description="Response data")
    error: Optional[Dict[str, Any]] = Field(None, description="Error details if success is False")
    meta: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")

    class Config:
        json_encoders = {
            ObjectId: str,
            datetime: lambda v: v.isoformat() if v else None
        }
        json_dumps = json.dumps
        json_loads = json.loads

class ErrorResponse(ApiResponse[None]):
    """
    Standard error response model.
    
    Attributes:
        success: Always False for error responses
        error: Dictionary containing error details
    """
    success: bool = Field(False, description="Always False for error responses")
    error: Dict[str, Any] = Field(..., description="Error details")

class PaginatedResponse(ApiResponse[List[T]]):
    """
    Paginated response model for list endpoints.
    
    Attributes:
        data: List of items in the current page
        pagination: Dictionary containing pagination metadata
    """
    data: List[T] = Field(..., description="List of items")
    pagination: Dict[str, Any] = Field(
        ...,
        description="Pagination details including total, page, and per_page"
    )

def success_response(
    data: Any = None,
    status_code: int = status.HTTP_200_OK,
    meta: Optional[Dict[str, Any]] = None,
    headers: Optional[Dict[str, str]] = None
) -> JSONResponse:
    """
    Create a successful API response.
    
    Args:
        data: The response data to include
        status_code: HTTP status code (default: 200)
        meta: Additional metadata to include in the response
        headers: Custom headers to include in the response
        
    Returns:
        JSONResponse: A FastAPI JSON response with the success format
    """
    response_data = {
        "success": True,
        "data": data,
    }
    
    if meta:
        response_data["meta"] = meta
    
    return JSONResponse(
        content=response_data,
        status_code=status_code,
        headers=headers or {}
    )

def error_response(
    message: str,
    status_code: int = status.HTTP_400_BAD_REQUEST,
    error_code: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None,
    headers: Optional[Dict[str, str]] = None,
    meta: Optional[Dict[str, Any]] = None
) -> JSONResponse:
    """
    Create an error API response.
    
    Args:
        message: Human-readable error message
        status_code: HTTP status code (default: 400)
        error_code: Machine-readable error code (default: HTTP_{status_code})
        details: Additional error details
        headers: Custom headers to include in the response
        meta: Additional metadata to include in the response
        
    Returns:
        JSONResponse: A FastAPI JSON response with the error format
    """
    error_data = {
        "success": False,
        "error": {
            "message": message,
            "code": error_code or f"HTTP_{status_code}",
        }
    }
    
    if details:
        error_data["error"]["details"] = details
    
    if meta:
        error_data["meta"] = meta
    
    return JSONResponse(
        content=error_data,
        status_code=status_code,
        headers=headers or {}
    )

def not_found_response(
    resource: str = "Resource",
    id: Optional[str] = None,
    headers: Optional[Dict[str, str]] = None
) -> JSONResponse:
    """
    Create a 404 Not Found error response.
    
    Args:
        resource: The type of resource that was not found
        id: The ID of the resource that was not found
        headers: Custom headers to include in the response
        
    Returns:
        JSONResponse: A 404 error response
    """
    message = f"{resource} not found"
    if id:
        message += f" with ID: {id}"
    
    return error_response(
        message=message,
        status_code=status.HTTP_404_NOT_FOUND,
        error_code="not_found",
        headers=headers
    )

def validation_error_response(
    errors: List[Dict[str, Any]],
    status_code: int = status.HTTP_422_UNPROCESSABLE_ENTITY,
    headers: Optional[Dict[str, str]] = None
) -> JSONResponse:
    """
    Create a validation error response.
    
    Args:
        errors: List of validation errors
        status_code: HTTP status code (default: 422)
        headers: Custom headers to include in the response
        
    Returns:
        JSONResponse: A validation error response
    """
    return error_response(
        message="Validation Error",
        status_code=status_code,
        error_code="validation_error",
        details={"fields": errors},
        headers=headers
    )

def paginated_response(
    items: List[Any],
    total: int,
    page: int,
    per_page: int,
    status_code: int = status.HTTP_200_OK,
    meta: Optional[Dict[str, Any]] = None,
    headers: Optional[Dict[str, str]] = None
) -> JSONResponse:
    """
    Create a paginated API response.
    
    Args:
        items: List of items for the current page
        total: Total number of items across all pages
        page: Current page number (1-based)
        per_page: Number of items per page
        status_code: HTTP status code (default: 200)
        meta: Additional metadata to include in the response
        headers: Custom headers to include in the response
        
    Returns:
        JSONResponse: A paginated response with the items and pagination metadata
    """
    response_data = {
        "success": True,
        "data": items,
        "pagination": {
            "total": total,
            "page": page,
            "per_page": per_page,
            "total_pages": (total + per_page - 1) // per_page if per_page > 0 else 0,
            "has_next": (page * per_page) < total,
            "has_prev": page > 1
        }
    }
    
    if meta:
        response_data["meta"] = meta
    
    return JSONResponse(
        content=response_data,
        status_code=status_code,
        headers=headers or {}
    )